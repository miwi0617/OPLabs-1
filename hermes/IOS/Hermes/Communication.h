//
//  Communication.h
//  Hermes
//
//  Created by Nicolas Charles Herbert Broeking on 1/18/15.
//  Copyright (c) 2015 NicolasBroeking. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface Communication : NSObject <NSURLConnectionDelegate>
{
    bool started;
    bool shouldRun;
    
}

@property(strong, atomic) NSThread *thread;

//Singleton
+(Communication*) getComm;

//Initilizer for the communication thread
-(instancetype)init;

//Main loop for the communication sub system
-(void) threadMain;

//Start the subsystem
-(void) start;

//stop the subsystem
-(void) stop;

//Force stop the subsystem
-(void) forceStop;

//Checks to see if the sub system is running
-(BOOL) isRunning;

//Methods for Communicating with the server
-(void) login:(id) sender;

//Starts a test for the mobile
-(void) startTest;


@end
