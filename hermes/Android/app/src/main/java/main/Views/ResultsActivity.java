package main.Views;

import android.app.AlertDialog;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.ServiceConnection;
import android.nfc.Tag;
import android.os.Bundle;
import android.os.IBinder;
import android.util.Log;
import android.view.KeyEvent;
import android.view.MenuItem;
import android.view.View;
import android.widget.Toast;

import com.oplabs.hermes.R;

import main.helpers.HermesActivity;
import tester.TestResults;
import tester.TestService;
import tester.TestState;

//This class controls the activity that has two fragments
//The animation fragment and the results fragment.
//It will switch between the two depending on what state we are in
//It also controls starting and stoping the testing subsystem and service
public class ResultsActivity extends HermesActivity {

    private final String TAG = "HermesResultsActivity";
    private boolean testBound;
    private TestService testService;

    // When created we init everything to a empty state and set the fragment to be
    //the animation fragment
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Log.i(TAG, "OnCreate");
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_results);
        if (savedInstanceState == null) {
            getFragmentManager().beginTransaction()
                    .add(R.id.FrameLayout, new AnimationFragment())
                    .commit();
        }
        testBound = false;
        testService = null;
    }

    //Called when the activity starts.
    //We check what state we are in and edit the fragments accordingly
    public void checkStatus()
    {
        TestState stateMachine = TestState.getInstance();
        TestResults latestResults = stateMachine.getPhoneResults();

        //Start Testing Process if IDLE
        if(stateMachine.getState() == TestState.State.IDLE)
        {
            Log.i(TAG, "We are IDLE");
            getFragmentManager().beginTransaction()
                    .replace(R.id.FrameLayout, new AnimationFragment())
                    .commit();
            //Tell Tester that we have prepared
            testService.startTest();
        }
        else if( stateMachine.getState() == TestState.State.PREPARING)
        {
            Log.i(TAG, "We are preparing");
            //We are preparing to Run a Test
            getFragmentManager().beginTransaction()
                    .replace(R.id.FrameLayout, new AnimationFragment())
                    .commit();

        }
        else if(stateMachine.getState() == TestState.State.COMPLETED)
        {
            //Get Results and move to results fragment
            Log.i(TAG, "We are completed");

            getFragmentManager().beginTransaction()
                    .replace(R.id.FrameLayout, new ResultsFragment(), "ResultsFrag")
                    .commit();
        }
        else
        {
            //We are in a testing state and we should update the view to show animation
            Log.i(TAG, "We are TESTING");
        }
    }

    //On start we need to check our state and subscribe to testing broadcasts
    @Override
    protected void onStart() {
        super.onStart();
        Log.i(TAG, "OnStart");

        /*NOTE: The Hermes Activity will check to see that we are still logged in*/
        startService(new Intent(this, TestService.class));
        Intent intent = new Intent(this, TestService.class);
        bindService(intent, testConnection, Context.BIND_AUTO_CREATE);

        //Set up broadcast receiver
        IntentFilter filter = new IntentFilter();
        filter.addAction("TestCompleted");
        filter.addAction("ReportRouter");
        registerReceiver(receiver, filter);
    }
    //On stop we clean up our broadcast requests and our states
    @Override
    protected void onStop() {
        super.onStop();
        Log.i(TAG, "OnStop");

        if(!(testService == null)) {
            unbindService(testConnection);
            if (TestState.getInstance().getState() == TestState.State.IDLE  ||
                    TestState.getInstance().getState() == TestState.State.COMPLETED) {
                stopService(new Intent(this, TestService.class));
            }
        }

        //Tell the communication system to stop all loops
        if(commService != null) {
            commService.clear();
        }
        //Stop listening for broadcasts
        unregisterReceiver(receiver);
    }

    //When the back button is pressed we report the results page as being viewed
    @Override
    public void onBackPressed() {
        Log.d(TAG, "On back pressed");
        if(TestState.getInstance().getState() == TestState.State.COMPLETED){
            TestState.getInstance().setState(TestState.State.IDLE,false);

        }
        super.onBackPressed();
    }

    //We want to go straight to settings if this is ever called in this view.
    //The only thing that could cause this method to get called is an error
    public void goToLogin(View view) {
        //Temporary until we get a login page
        goToSettings(view);
    }

    //We transfer control to the settings activity. Can be called either on error or on button press
    public void goToSettings(View view) {
        Intent intent = new Intent(this, SettingsActivity.class);
        intent.putExtra(SettingsActivity.EXTRA_SHOW_FRAGMENT, SettingsActivity.GeneralPrefs.class.getName());
        intent.putExtra(SettingsActivity.EXTRA_NO_HEADERS, true);
        startActivity(intent);
    }

    //Show the about page
    @Override
    public void goToAbout(View view) {
        Intent intent = new Intent(this, AboutTestsActivity.class);
        startActivity(intent);
    }

    //Reports a bind and unbind from the service
    protected ServiceConnection testConnection = new ServiceConnection() {
        public void onServiceConnected(ComponentName className, IBinder service) {
            TestService.MyLocalBinder binder = (TestService.MyLocalBinder) service;
            testService = binder.getService();
            testBound = true;
            testService.setCommunicator(commService);
            checkStatus();
        }
        public void onServiceDisconnected(ComponentName arg0) {
            testBound = false;
            testService = null;
        }
    };

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case android.R.id.home:
                onBackPressed();
                break;

        }
        return super.onOptionsItemSelected(item);
    }
    //Used to receive broadcasts from the testing subsystem
    private BroadcastReceiver receiver = new BroadcastReceiver() {

        @Override
        public void onReceive(Context context, Intent intent) {
            // Implement code here to be performed when
            // broadcast is detected
            Log.i(TAG, "Received Intent");

            TestResults results = intent.getParcelableExtra("Results");
            if( !results.isValid())
            {
                TestState.getInstance().setState(TestState.State.IDLE, false);
                //Display Error
                new AlertDialog.Builder(ResultsActivity.this)
                        .setTitle("Testing Error")
                        .setMessage("There was an error running a test. Please check your internet connection and try again.")
                        .setPositiveButton("Ok", new DialogInterface.OnClickListener() {
                            public void onClick(DialogInterface dialog, int which) {
                                //Do nothing
                                ResultsActivity.this.finish();
                                Log.e(TAG, "Should be finished");
                            }
                        })
                        .setIcon(R.drawable.ic_launcher)
                        .show();


            }
            else{
                if( intent.getAction().equals("TestCompleted"))
                {
                    checkStatus();
                }
                else
                {
                    Log.e(TAG, "Unknown Broadcast type: " + intent.getAction());
                }
            }
        }
    };
}
