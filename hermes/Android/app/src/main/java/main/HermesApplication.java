package main;

import android.util.*;
import android.app.Application;
import android.content.res.Configuration;

public class HermesApplication extends Application 
{
	private final String TAG = "HermesApp";

	public HermesApplication(){
		super();
		Log.i(TAG, "Application object was constructed");
	}
	@Override
	public void onConfigurationChanged(Configuration newConfig) {
		super.onConfigurationChanged(newConfig);
	}
 
	@Override
	public void onCreate() {
		super.onCreate();
		Log.i(TAG, "Application onCreate");

		//Start Services

	}
	
	@Override
	public void onLowMemory() {
		super.onLowMemory();
		Log.w(TAG, "Application has low memory");
	}
 
	@Override
	public void onTerminate() {
        Log.i(TAG, "Application will Terminate");
		super.onTerminate();

        //Stop Services
	}
}
