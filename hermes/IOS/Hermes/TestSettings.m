//
//  TestSettings.m
//  Hermes
//
//  Created by Nicolas Broeking on 4/11/15.
//  Copyright (c) 2015 NicolasBroeking. All rights reserved.
//

#import "TestSettings.h"

@implementation TestSettings
@synthesize validDomains, invalidDomains, DNSServer, mobileResultID, setId, routerTesultID, timeout;

-(void) addInvalidDomain: (NSString*) string
{
    [invalidDomains addObject:string];
}
-(void) addValidDomain: (NSString*)string
{
    [validDomains addObject:string];
}
@end