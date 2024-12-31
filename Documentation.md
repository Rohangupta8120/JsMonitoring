## Feature List
* [x] Simple JS Monitoring
* [x] HTML Page JS Filename Extraction 
* [x] Git Upload/Diffing
* [x] JS Beautification
* [x] Discord Notifications
* [X] API/UI
* [ ] Headless Browser/Mapperplus to Automatically Handle Webpack Stuff
* [ ] Use Chrome's Recorder to Record Auth Modules
* [ ] HTML Page JS Filename Extraction with Auth Module
* [ ] HTML Page JS Filename Extraction with Provided Cookies and Session Refresh Module

## Installation
First we will need to install all the requirements with `pip install -r requirements.txt`.
This project also relies on `pprettier` to beautify the JS files. You can install it with `npm install -g @mixer/parallel-prettier`.

Next, we will need to create a git repository to store our monitored files in. This should probably be a private repository and use private key based authentication (without a password) to push to it. The repository name can be overridden in each procurement module by changing the `gitRepoDir` variable, but id recommend keeping it named `kanshiFiles`.
So, clone that into the base of this project with `git clone ssh://git@github.com/YOUR_GITHUB_USERNAME/kanshiFiles.git`.

Next, we'll do the preliminary run of `knsh.py` which will build the DB. 
`./knsh.py`
You should see the following output:
```
Building DB
```

You will then need to create a procurement module (see terminology below). This can be done by copying `templateProcurementModule.py` into the `procurementModules` directory and modifying it to your needs. See the comments in the template file for more information.

From there, you can add a file monitor with the following command:
```
./knsh.py add -t "Title" -b "https://bugcrowd.com/engagements/Company" -c "Company" -f 5 -m "./procurementModules/companyMainJs.py"
```

This will add the file monitor to the DB and then you can run `./knsh.py` to start monitoring the file:
```
./knsh.py run
```
You'll want to set this on a cronjob to run every minute. If there are no pending tasks, then it will just exit.

Now, you can go to the `kanshiFiles` repository and see the files that have been monitored. The alerts will be sent to the discord webhook and in the UI dashboard.

## API/UI

If you'd like to use the Kanshi UI, you can run `./kanshiapi.py` and then navigate to `http://localhost:8083/dashboard.html` in your browser. From there, you can see all of the alerts, file monitors, etc. You can also claim various alerts to your table if you're working as a team.

Note: You will need to update `dashboard.html` with your github username if you want to link to your commits.

## Sub Files
There is a bit of a half-baked functionality for sub files (chunked JS files) in place. You can provide a regex to extract the sub file name and url from the main file. This can be used with the `subFileDataGenerator` function in the procurement module to make sure the correct name is generated. From there, the sub file will be monitored and the alerts will be sent to the discord webhook and in the UI dashboard. We're hoping to get some better functionality for this in the future.


##   Terminology
* `fileMonitor`: A file monitor is a database entry that contains the configuration for a JS file that will be monitored.
* `procurementModule`: A procurement module is a python program that will be used to retrieve the JS file that will be monitored. In the simples case, this will just be a static file. In a more complex case, the JS file may have to be extract from an HTML page or retrieved via an auth module/session refresh module.
* `alert`: An alert is a database entry that contains the details of a change in the JS file.
* `authModule`: An auth module is a python program that will be used to authenticate the user with the target.
* `sessionRefreshModule`: A session refresh module is a python program that will be used to refresh the session with the target.


## Files
`knsh.py` is the main command line interface for Kanshi. It is the file that will be run to start Kanshi.

`kanshiapi.py` is the file that will be run to start the Kanshi API. This API will be used to interact with the Kanshi UI.

`base.py` is the file that will be run by `knsh.py` in conjunction with a procurement module to detect changes in the JS files.

`templateProcurementModule.py` is the file that contains the template for a procurement module. A procurement module is a python program that will be used to retrieve the JS file that will be monitored.

## Configuration Types
Within Kanshi there are several types of monitoring configurations:
* Simple JS Monitoring
* HTML Page JS Filename Extraction 
* HTML Page JS Filename Extraction with Auth Module
* HTML Page JS Filename Extraction with Provided Cookies

These 4 different configurations describe the different ways the Kanshi will retrieve the JS file that will be monitored.

### Simple JS Monitoring
This is the simplest of the four types. In this case, no authentication or extraction of the JS file name. There is simply a file such as `main.js` which is updated with the most recent version of the JS contents. In this situation, simply provide Kanshi with a URL and time period and that file will be monitored.


### HTML Page JS Filename Extraction 
In this type, the JS file changes with each new version of the software (for example, it contains a hash or something of the like). In this scenario, we must provide Kanshi with a consistent page from which the JS file location name can be extracted with a regular expression, and then to a regular expression to do the extraction. Once this is in place, Kanshi will reach out to the specified page, extract the JS file name, and then proceed to monitor that JS file. 


### HTML Page JS Filename Extraction with Auth Module (Not Implemented)
When the JS file name must be extracted from a page that requires authentication then an authentication module must be utilized. An authentication module is a python program that will return the cookies required to extract the JS file. First, this authentication module will be run, the user will be authenticated, then the JS file name will be extracted and monitored.

### HTML Page JS Filename Extraction with Provided Cookies and Session Refresh Module (Not Implemented)
The worst-case scenario is that there is a CAPTCHA or something that requires human interaction in order to log in. In this scenario, the user's cookies should be inputted directly into Kanshi. Kanshi will then use these cookies for as long as possible to retrieve the JS files and when the session has expired, it will alert the administrators to the fact that it no longer is able to monitor this target. The administrator will re-authenticate and provide new cookies to Kanshi.

Another feature for this section is Session Refresh Modules. These modules, much like auth modules, will take the current cookies and attempt to refresh the session in an attempt to prevent the administrator from having to log back in. If successful, these modules may be able to extend the session indefinitely, resulting in less work for the administrator.