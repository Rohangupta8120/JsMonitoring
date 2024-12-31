### Configuration Settings
def subFileDataGenerator(mainUrl, subFileInput, subFileName):
    # return (formatted name of file, url of file)
    return (subFileName.format(subFileInput.split("/")[-1].split("-")[0]),
            "/".join(mainUrl.split("/")[:-2])+subFileInput)

global debug
# Set debug to True to enable debug logging
debug = False

# The name of the pickle file which is stored in /procurementModules
pickleName = "rhynorater.pickle"

# The URL where the JS file(s) URLs are extracted from
procUrl = "https://poc.rhynorater.com/kanshiExample/monitorExample.html"

# Discord webhook URL for sending alerts
discordWebhook = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"

# Abitrary name for the module
moduleName = "RhynoraterTesting"

jsFiles = {
    #Give each JS file a name
    "targetMainApp.js":{
        #Set customDirName to the name of the directory you want to store the file in - will default to the filename if not set
        #"customDirName":"yoyo",
        #Set dynamicName to True if the name changes with each iteration
        "dynamicName":True,
        #Set alertOnFileChange to True if you want to be alerted when the file changes
        "alertOnFileChange":False,
        #If the file is static, comment out jsRegex and just use `url`
        #"url":"https://site.com/main.js",
        #Provide the regex for the JS file extraction
        "jsRegex":"src=\"(/[^\"]+)\"",
        #Set urlBase to the base path that should be prepended to the extracted value from jsRegex
        "urlBase":"https://site.com/static/",
        "regexes":{
            #Name each regex and provide the required metadata.
            # NOTE: regexes are applied before beautification.
            "New Endpoint":{
                "regex": '"(/[^"]+)"',
                "severity": "Medium",
                "beautify": False,
                "filename":"yoyo-endpoints.txt",
                "alertTitle": "New endpoints found for yoyo!"
            },
            "New SubFile":{ #Feel free to remove this if you dont need sub files.
                "regex": '"(/kanshiExample/subfile[^"]+)"',
                "severity": "Medium",
                "beautify": False,
                "filename":"subfilesDiscovered.txt",
                "alertTitle": "New Subfile found!",
                "alertOnFileChange":False,
                "subFileTemplate":{
                    "nameBase":"kanshiSubFile-{}.js",
                    "dynamicName":True,
                    "alertOnFileChange":False,
                    "regexes":{
                        "New Endpoint":{
                            "regex": '"(/[^"]+)"',
                            "severity": "Medium",
                            "beautify": False,
                            "filename":"{}-endpoints.txt",
                            "alertTitle": "New endpoints found for subfile!"
                        }
                    }
                },
                "isSubFile": True
            }
        }
    }
}
###
gitRepoDir = "./kanshiFiles/"
moduleDir = gitRepoDir+"{}/".format(moduleName)

exec(open("./base.py").read())

if __name__ == "__main__":
    debug=True
    print(json.dumps(run("test", "test"), indent=4))

