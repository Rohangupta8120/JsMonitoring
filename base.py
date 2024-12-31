from curl_cffi import requests
import re
import pickle
import os
import hashlib
import git
import datetime
import copy
import subprocess
import json
import shutil

def procure():
    # Hit the endpoint to extract the JS files we want
    global debug
    if debug: print("Reaching out to procUrl: "+procUrl)
    r = requests.get(procUrl, verify=False, allow_redirects=True, impersonate="chrome")
    jsFileNames = {}

    for f in jsFiles.keys():# For each file we should extract
        if 'jsRegex' in jsFiles[f]: # If the file requires a regex, grab the filenames
            urls = re.findall(jsFiles[f]['jsRegex'], r.content.decode("utf-8"))
            if debug: print("Regex results: "+",".join(urls))
            if not urls:
                raise Exception("Invalid JS File Procurement Regex")
            jsFileNames[f] = {"url":urls[0]}
        else: # Otherwise, the filename is static, just add it to the output
            jsFileNames[f] = {"url":jsFiles[f]['url']}
    return jsFileNames


def quickLog(text):
    # Quickly send notification if things are going wrong
    requests.post(discordWebhook,
            data=json.dumps({"content":"[LOG] "+text}), headers={"Content-Type":"application/json"})


def gitFileNormalize(filename):
    # make the URL relative to the git repo
    if filename.startswith(gitRepoDir):
        filename = filename[len(gitRepoDir):]
    if filename.startswith("./"):
        filename = filename[2:]
    return filename

def beautifyFile(filename):
    # beautify the file using @mixer/parallel-prettier
    pploc = subprocess.check_output(["which", "pprettier"]).strip().decode("utf-8")
    r = subprocess.run(["node", pploc, filename, "--write"])
    if r.returncode==1:
        print("Unable to beautify file: "+filename);
        quickLog("Unable to beautify file: "+filename)
    return True


def writePushFile(filename, content, commitMessage, currentTime, writeVersion=False):
    #Adds a writes a file (and potentially its version backup) to the git repo. Also, manages beautifing
    if os.path.exists(filename): # Dont write the file if there is no content.
        rf = open(filename, "r", encoding="utf-8")
        d = rf.read()
        rf.close()
        if d == content:
            print("File has no new content... "+filename);
            quickLog("File has no new content... "+filename)
            return False
    global debug
    if debug: print("Writing {} with versioning {} and commitMessage {}.".format(filename, writeVersion, commitMessage))
    # Write the file
    wf = open(filename, "w", encoding="utf-8")
    wf.write(content)
    wf.close()
    # if the file is a JS file, beautify that
    if filename.endswith(".js"): beautifyFile(filename)
    # add,commit, and push to git repo
    repo = git.Repo(gitRepoDir)
    repo.index.add(gitFileNormalize(filename))
    repo.index.commit(commitMessage)
    cHash = repo.head.object.hexsha
    origin = repo.remote(name="origin")
    origin.push()
    # this writeVersion functionality allows us to store a version of the file associated with a specific timestamp and hash
    # so that in the future, if we want to search accross all versions, we can do that easily since searching accross git history
    # is not really something that most tools(ie, sourcegraph and github) like to do.
    if writeVersion:
        vFilename =os.path.dirname(filename)+"/versions/"+currentTime+"_"+repo.head.object.hexsha+"_"+filename.split("/")[-1]
        shutil.copy(filename, vFilename)
        repo.index.add(gitFileNormalize(vFilename))
        repo.index.commit("Adding version file for "+repo.head.object.hexsha)
        origin = repo.remote(name="origin")
        origin.push()
    return cHash

def handleFile(bbpUrl, company, f, jsFileName, jsFile, lastRun, currentTime, isSubFile=False):
    global debug
    alerts = []
    subFiles = []
    # If this is a relative file, fill in the URL by using the `urlBase` attribute in the file/subfile definition
    if "urlBase" in jsFile: jsFileName['url'] = jsFile['urlBase']+jsFileName['url']
    if f in lastRun and jsFileName['url'] == lastRun[f]['url'] and jsFile['dynamicName']:
        # Skip this file - no changes. If there had been changes, then the hash have changed since dynamicName is set to True.
        print("{} - No Changes Detected: Same name extracted New:{} Old:{}".format(f, jsFileName['url'], lastRun[f]['url']))
        return (lastRun[f], alerts, subFiles)
    elif f in lastRun:
        lastRun[f]['url'] = jsFileName['url']

    if debug: print("Handling this file: "+jsFileName['url'])
    r = requests.get(jsFileName['url'], verify=False, impersonate="chrome")
    if r.status_code!=200:
        print("Unable to retrieve file: "+jsFileName['url']+" Status code: "+str(r.status_code));
        quickLog("Unable to retrieve file: "+jsFileName['url']+" Status code: "+str(r.status_code));
        return (lastRun[f], alerts, subFiles)
    rContent = r.content.decode("utf-8")
    if debug: print("File content: "+rContent[:min(len(rContent), 50)])
    if 'Content-Length' in r.headers:
        jsFileName['length'] = r.headers['Content-Length']
        if f in lastRun and 'length' in lastRun[f] and lastRun[f]['length'] == jsFileName['length']:
            # Skip this file - no changes. If there had been changes, the content-length would (likely) be different.
            print("{} - No Changes Detected: Same content length".format(f))
            return (lastRun[f], alerts, subFiles)
        elif f in lastRun and 'length' in lastRun[f] and lastRun[f]['length'] != jsFileName['length']:
            #The length has changed, modify lastRun just in case last-modifies triggers. It wont matter anyway if it doesn't return in Last-Modified
            lastRun[f]['length'] = jsFileName['length']
    if 'Last-Modified' in r.headers:
        jsFileName['lastModified'] = r.headers['Last-Modified']
        if f in lastRun and 'lastModified' in lastRun[f] and lastRun[f]['lastModified'] == jsFileName['lastModified']:
            # Skip this file - no changes. If there had been changes, the lastModified would (likely) be different.
            print("{} - No Changes Detected: Same Last-Modified date".format(f))
            return (lastRun[f], alerts, subFiles)

    # Define the directory to output the file to. This can be defined two ways:
    # 1. using the `customDirName` attribute. If this is the case, then this is the directory name under the moduleDir that will be used
    # 2. if the `customDirName` is not defined, then the filename will be used with `.js` removed. this is calculated using the `subFileDataGenerator`
    #    function for subfiles.
    outputDir = moduleDir+(jsFile['customDirName'] if ('customDirName' in jsFile and jsFile['customDirName']) else f.replace(".js", ""))
    outputDir += "/"
    # we ensure that the output directory, and required versions and regex directories are created
    os.makedirs(outputDir, exist_ok=True)
    os.makedirs(outputDir+"versions", exist_ok=True)
    os.makedirs(outputDir+"regexes", exist_ok=True)
    # write the file - since this is a JS file, we will write an additional version as well.
    fcHash = writePushFile(outputDir+f, rContent, "New file Detected: "+jsFileName['url'], currentTime, writeVersion=True)
    if not fcHash:
        print("{} - No Changes Detected: Same file".format(f))
        if f not in lastRun:
            return (jsFileName, alerts, subFiles)
        return (lastRun[f], alerts, subFiles)
    if 'alertOnFileChange' in jsFile and jsFile['alertOnFileChange']:
        if not isSubFile:
            alerts.append((fcHash,
                bbpUrl,
                company,
                "File Change: {} - {}".format(f, jsFileName['url']),
                jsFileName['url'],
                jsFile['jsRegex'],
                datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "Informational",
                "unseen",
                None,
                None))
        else:
            alerts.append((fcHash,
                bbpUrl,
                company,
                "File Change: {} - {}".format(f, jsFileName['url']),
                jsFileName['url'],
                "Subfile Regex",
                datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "Informational",
                "unseen",
                None,
                None))

    jsFileName['regexes'] = {}
    for reg in jsFile['regexes']:
        if debug: print("Running regex: "+jsFile['regexes'][reg]['regex'])
        # Find all the results of the regex search
        res = list(set(re.findall(jsFile['regexes'][reg]['regex'], rContent)))
        if debug: print("Regex results: "+str(res))
        # Hash all the results to see if there are any changes
        jsFileName['regexes'][reg] = list(map(lambda d: hashlib.sha256(d.encode("utf-8")).hexdigest(), res))
        # if there is a last run and these results are not a subset of the past results
        if not (f in lastRun and reg in lastRun[f]['regexes'] and set(jsFileName['regexes'][reg]).issubset(set(lastRun[f]['regexes'][reg]))):
            fn = outputDir+"regexes/"+jsFile['regexes'][reg]['filename'] #<-- this `filename` will have a {} spot if this is a subfile
            # If this file is a subfile, then we'll need to use the `subFileName` to create the filename (ie, insert `subFileName` into `filename`)
            if isSubFile: fn=fn.format(jsFile['subFileName'].replace('.js', ''))
            # Writing the regex file, with no version history written
            cHash = writePushFile(fn, "\n".join(res), "{} - {}".format(f, jsFile['regexes'][reg]['alertTitle']), currentTime)
            if not cHash:
                print("{} - No Changes Detected: Same file".format(f))
                continue
            # if a regex is defined as `isSubFile`, we can also define a custom `alertOnFileChange` attribute to control whether we alert on new subfile names
            if not ("isSubFile" in jsFile['regexes'][reg] and
                    jsFile['regexes'][reg]['isSubFile'] and
                    "alertOnFileChange" in jsFile['regexes'][reg] and
                    not jsFile['regexes'][reg]['alertOnFileChange']):
                alerts.append((cHash,
                    bbpUrl,
                    company,
                    "{} - {}".format(f, jsFile['regexes'][reg]['alertTitle']),
                    jsFileName['url'],
                    reg,
                    datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    jsFile['regexes'][reg]['severity'],
                    "unseen",
                    None,
                    None))
        # if this regex results in a sub file, then we'll need to copy the subFileTemplate struct and send that to the subFiles array to be processed by the loop in main
        if "isSubFile" in jsFile['regexes'][reg]:
            for subData in res:
                o = copy.copy(jsFile['regexes'][reg]['subFileTemplate'])
                o['subFileData'] = subData
                o['subFileName'], o['url'] = subFileDataGenerator(jsFileName['url'], subData, o['nameBase'])
                subFiles.append(o)

    return (jsFileName, alerts, subFiles)


def run(bbpUrl, company):
    ## Procure the JS file names/locations
    jsFileNames = procure()
    currentTime = datetime.datetime.utcnow().strftime("%d%b%Y-%H:%M")
    alerts = []
    lastRun = {}
    subFiles = []
    if os.path.exists("./procurementModules/"+pickleName): #Load the previous database for the lastRun
        lastRun = pickle.load(open("./procurementModules/"+pickleName, "rb"))

    global debug
    if debug: print("Running these files: "+str(jsFileNames))
    for f in jsFileNames.keys(): # For each file extracted from procure(), retrieve the files and check for changes/alerts/subfiles
        jsFileNames[f],_alerts,_subFiles =  handleFile(bbpUrl, company, f, jsFileNames[f], jsFiles[f], lastRun, currentTime)
        alerts += _alerts
        subFiles += _subFiles

    if debug: print("Running these subfiles: "+str(subFiles))
    # Each iteration of the above might add more subfiles, we need to process these as the were true files except isSubFile=True
    for f in subFiles:
        finput = {'url':f['url']}
        jsFileNames[f['subFileName']], _alerts, _ = handleFile(bbpUrl, company, f['subFileName'],finput, f, lastRun, currentTime, isSubFile=True)
        alerts += _alerts

    pickle.dump(jsFileNames, open("./procurementModules/"+pickleName, "wb"))
    return alerts
