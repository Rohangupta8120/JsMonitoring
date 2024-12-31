## Kanshi - Authenticated JS Monitoring Framework

The goal of Kanshi (監視) is to provide an interface for monitoring changes in an application's JS files over time for the purposes of assessing that app's security posture. 

See [Documentation.md](Documentation.md) for more information.


### Goals
The goals for this project include the following:

- [x] Provide a robust command-line or GUI interface for management
- [x] Allow for efficient search of historical data to watch a products progression over time
- [x] Issue alerts when interesting changes have been found
- [ ] Allow for easy handling of authentication through authentication modules and session refresh modules


### Concept
This concept for this project is that since bug bounty hunters often move from app to app, we lose the depth of understanding of the app that we had when we were doing a deep dive. Thus it is harder for us to go back and notice the changes that have occurred since we last attacked this app. Using Kanshi, once a bug bounty hunter has assessed an app thoroughly and understands the relationship between entries in JavaScript files and functionality in the application, they should define this relationship in Kanshi so that any changes to these sections of the JavaScript files can be noted and alerted on. That way, an attacker can use their prior knowledge of the application to make testing more efficient in the future.

Another benefit of Kanshi is that it allows for diffs over time of pivotal JavaScript files. This allows the attacker to go back in time and use historical data to try to break the current configuration of the application.

While not integrated into Kanshi, it will likely be most efficient to use Kanshi in conjunction with detailed notes on the application in order for the attacker to be able to quickly refresh their memory on the attack surface when an alert is received.

### Implementation
The current implementation allows for a user to define a page from which a JS file is extracted. From there, that JS file's changes are tracked and a series of regexes are applied. These regex extract interesting values. Alerts are made based off the changes in the values. 
