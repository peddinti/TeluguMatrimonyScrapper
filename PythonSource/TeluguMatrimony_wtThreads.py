import datetime
import sys
import urllib
import urllib2 
from urllib2 import Request, build_opener, HTTPCookieProcessor, HTTPHandler
import cookielib
import xml.dom.minidom
import re
import json
import HTMLParser
import random
import threading
import time
import copy
from bs4 import BeautifulSoup
import codecs
############################################################################################################################################
######################################################## Global Variables ##################################################################
############################################################################################################################################


Usage = "python TeluguMatrimonyScrapper <config file> \n OR \n python TeluguMatrimonyScrapper -FillMissing <config file> <tsv file>"
ConfigFileName = None
InputTsvFileName = None
MissFilling = False;
MakeHoroscopeRequestFromUser = False;

TNoRegex =re.compile("\\((T\\d+)\\)")
searchTNoListRegex = re.compile('"perpage_ids"\s*:\s*"([T\d,]+)"')

# telugu matrimony urls
HoroscopeIntermediateUrlTemplate = "http://profile.telugumatrimony.com/horoscope/horoviewintermediate.php?ID={0}&PID={0}&source=generate"
HoroscopeUrlTemplate = "http://image.telugumatrimony.com/horoscopegen/{0}/{1}/MHENG{2}.html";

RequestHoroscopeUrl = "http://profile.telugumatrimony.com/request/bmrequestfor.php";
SearchUrl = "http://profile.telugumatrimony.com/search/fetchrsearchresult.php";
ProfileUrlTemplate = "http://profile.telugumatrimony.com/profiledetail/viewprofile.php?id={0}";
LoginUrl = "https://secure.telugumatrimony.com/login/memlogin.php";

# THE TEMPLATE IS VERY SPECIFIC TO A USER.
SearchPostSuffixTemplate = "&PHOTO_OPT=N&HOROSCOPE_OPT=N&IGNORE_OPT=N&CONTACT_OPT=N&VIEW_OPT=N&SHORTLIST_OPT=N&DISPLAY_FORMAT=six&randid=a917993s&but_save=&SEARCH_TYPE=ADVANCESEARCH&SEARCH_ID=Mg==&ss=&wherefrom=frmpaging&facet=N&STLIMIT={0}";
TeluguMatrimonyCookies = cookielib.CookieJar()
AskGaneshCookies = cookielib.CookieJar()

MatchScoresUrl = "http://askganesa.com/services/free_horoscope/gun-milan-new1.aspx";
MatchScoresBoyDetails = "bname={0}&bdate={1}&bmonth={2}&byear={3}&bhour={4}&bmin={5}&bcountry={6}&bcity={7}&longitude={8}&ew={9}&latitude={10}&ns={11}&timediff={12}";
MatchScoresGirlDetails ="gname={0}&gdate={1}&gmonth={2}&gyear={3}&ghour={4}&gmin={5}&gcountry={6}&gcity={7}&glongitude={8}&gns={9}&glatitude={10}&gew={11}&gtimediff={12}";
MatchScoresPostRequestTemplate = "{0}&{1}&ayanamsa={2}&terms=0&B1=Submit";

RequestHoroscopePostRequestTemplate = "WID=YES&OID={0}&REQUESTFOR=2&ACTION=REQUESTFOR&closediv=cboxLoadedContent"

PlaceFinderUrl = "http://askganesha.com/hindi/place_finder.asp?act=find ";
PlaceFinderPostTemplate = "country={0}&city={1}&B1=Submit";

GoogleGeoCoderApiUrl = "https://maps.googleapis.com/maps/api/geocode/xml?address={0},%20{1}&sensor=false&key=AIzaSyD-WrDl5VHXznx7cG-gRWsDCNpa0cKqG2Y";

OutputHeaders = ["TNo", "Name","Age","Height","Eating Habits","Caste / Sub Caste","Gothram","Star / Raasi","Kuja Dosham","City","State","Country","Date of Birth","Time of Birth","Time Zone","Place of Birth","Varna","Vashya","Tara","Yoni","Graha","Gan","Bhakut","Nadi","Total Score"]

### Thread control parameters ###
threadMinCount = 5
threadMaxCount = 15
threadPollWait = 0.5
threadExecTime = 5
############################################################################################################################################
##################################################### End of Global Variables ##############################################################
############################################################################################################################################

ConfigParams ={};
UserBirthPlaceDetails = {};
UserBirthDateTime = None
OutputFile = None

def Test():
    global MissFilling
    MissFilling = True

def ParseCommandLineParams(args, Usage):
    ConfigFileName = None
    MissFilling = False
    InputTsvFileName = None
    OutputFile = None
    # python the first argument is the file name itself
    if len(args) <= 1:
        raise Exception(Usage)
        
    if args[1].lower() == "-fillmissing":
        if len(args) < 4:
            raise Exception(Usage)
        ConfigFileName = args[2]
        InputTsvFileName = args[3]
        if len(args) >= 5:
            OutputFile = open(args[4], "w")
        MissFilling = True
    else:
        if ConfigFileName == "-requesthoroscope":
            MakeHoroscopeRequestFromUser = True
            ConfigFileName = args[2]
            if len(args) >= 4:
                OutputFile = open(args[3], "w")
        else:
            ConfigFileName = args[1]
            if len(args) >= 3:
                OutputFile = open(args[2], "w")
    return (MissFilling, ConfigFileName, InputTsvFileName, OutputFile)

def ReadConfig(fileName):
    configParams = {}
    fileHandler = open(fileName, "r")
    for line in fileHandler:
        if not line.startswith(";"):
            cols = line.split('=')
            if len(cols) >= 2:
                configParams[cols[0]] = '='.join(cols[1:]).strip()
    # checking for all the requried values being present in the config file
    if (not  "TNo" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"TNo\". (the parameter names are case sensitive)")
    if (not  "Password" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"Password\". (the parameter names are case sensitive)")
    if (not  "SearchQuery" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"SearchQuery\". (the parameter names are case sensitive)")
    if (not  "Name" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"Name\". (the parameter names are case sensitive)")
    
    if (not  "Gender" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"Gender\". (the parameter names are case sensitive)")
    
    if (not  "DateOfBirth" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"DateOfBirth\". (the parameter names are case sensitive)")
    
    if (not  "TimeOfBirth" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"TimeOfBirth\". (the parameter names are case sensitive)")
                
    if (not  "CountryOfBirth" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"CountryOfBirth\". (the parameter names are case sensitive)")
                
    if (not  "CityOfBirth" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"CityOfBirth\". (the parameter names are case sensitive)")

    # Get user birth details
    UserBirthPlaceDetails = GetPlaceDetails_new(configParams["CountryOfBirth"], configParams["CityOfBirth"])
    
    try:
        UserBirthDateTime = datetime.datetime.strptime(configParams["DateOfBirth"] + " " + configParams["TimeOfBirth"], "%m-%d-%Y %H:%M")
    except ValueError:
        sys.stderr.write("Error parsing the User Date of Birth and Time of birth. Ignoring the data")
    
    return (configParams,UserBirthPlaceDetails, UserBirthDateTime)

def GetTeluguMatrimonyLoginCookies(tNo, password, TeluguMatrimonyCookies, LoginUrl):
    postContent = "ID={0}&PASSWORD={1}".format(tNo, password)
    MakePostRequest(LoginUrl, postContent, TeluguMatrimonyCookies);

def GetAskGaneshCookies():
    MakePostRequest("http://www.askganesha.com/services/free_horoscope/gun-milan.asp", "", AskGaneshCookies)

def GetUserProfile(TNo, TeluguMatrimonyCookies):
    global ProfileUrlTemplate
    
    profileUrl = ProfileUrlTemplate.format(TNo)
    
    return MakeGetRequest(profileUrl,TeluguMatrimonyCookies)
    
def GetUserDetails(TNo, TeluguMatrimonyCookies):
    userInfo = {}
    userProfile = GetUserProfile(TNo, TeluguMatrimonyCookies)
    htmlDoc = None
    if userProfile != None:
        htmlDoc = BeautifulSoup(userProfile)
    try:
        # Getting Details
        # Getting Personal Information
        # Getting Basic info
        basic_info_node = htmlDoc.find("div", class_="vp-basicinfo-icon").parent()[1].find_all("div", recursive=False)[1]
        keys = basic_info_node.select("div.fleft.width140")
        values = basic_info_node.select("div.fleft.colon")
        key_values = zip(keys, values)
        userInfo["Basic Details"] = {}
        for key_value in key_values:
            userInfo["Basic Details"][key_value[0].text.strip()] = key_value[1].text.strip()
        
        religious_info_node = htmlDoc.find("div", class_="vp-relgninfo-icon").parent()[1].find_all("div", recursive=False)[1]
        keys = religious_info_node.select("div.fleft.width140")
        values = religious_info_node.select("div.fleft.colon")
        key_values = zip(keys, values)
        userInfo["Religious Information"] = {}
        for key_value in key_values:
            userInfo["Religious Information"][key_value[0].text.strip()] = key_value[1].text.strip()
            
        location_info_node = htmlDoc.find("div", class_="vp-locinfo-icon").parent()[1].find_all("div", recursive=False)[1]
        keys = location_info_node.select("div.fleft.width140")
        values = location_info_node.select("div.fleft.colon")
        key_values = zip(keys, values)
        userInfo["Location"] = {}
        for key_value in key_values:
            userInfo["Location"][key_value[0].text.strip()] = key_value[1].text.strip()
        
        professional_info_node = htmlDoc.find("div", class_="vp-profinfo-icon").parent()[1].find_all("div", recursive=False)[1]
        keys = professional_info_node.select("div.fleft.width140")
        values = professional_info_node.select("div.fleft.colon")
        key_values = zip(keys, values)
        userInfo["Professional Information"] = {}
        for key_value in key_values:
            userInfo["Professional Information"][key_value[0].text.strip()] = key_value[1].text.strip()
        
        family_info_node = htmlDoc.find("div", class_="vp-famlyinfo-icon").parent()[1].find_all("div", recursive=False)[1]
        keys = family_info_node.select("div.fleft.width140")
        values = family_info_node.select("div.fleft.colon")
        key_values = zip(keys, values)
        userInfo["Family Details"] = {}
        for key_value in key_values:
            userInfo["Family Details"][key_value[0].text.strip()] = key_value[1].text.strip()
            
    except Exception:
        return userInfo
    return userInfo
    
def GetHoroscopeDetails(TNo, TeluguMatrimonyCookies):
    global HoroscopeUrlTemplate
    global HoroscopeIntermediateUrlTemplate
    horoscopeDetails = {};
    horoscopeUrl = HoroscopeUrlTemplate.format(TNo[1],TNo[2],TNo)
    horoscopeResponse = MakeGetRequest(horoscopeUrl, TeluguMatrimonyCookies)
    horoscopeNodes = None
    if (horoscopeResponse != None):
        horoscopeDoc = BeautifulSoup(horoscopeResponse)
        horoscopeNodes = [node for node in horoscopeDoc.find_all("div",class_="smalltxt") if node.text.startswith("Name")]
        
    if (horoscopeNodes != None and (len(horoscopeNodes) > 0)):
        horoscopeNode = horoscopeNodes[0]
        horoscope = Sanitize(horoscopeNode.text)
        horoscopeDetails = dict([(key.split(':')[0].strip(),':'.join(key.split(':')[1:]).strip()) for key in horoscope.split('|')])
    else:
        horoscopeIntermediateUrl = HoroscopeIntermediateUrlTemplate.format(TNo)
        horoscopeIntermediateResponse = MakeGetRequest(horoscopeIntermediateUrl, TeluguMatrimonyCookies)
        if (not horoscopeIntermediateResponse):
            return {}
        horoscope_object = re.match("<script>\s+window\.location\.href=\"(.+)\";</script>",horoscopeIntermediateResponse)
        if (horoscope_object == None):
            return {}
        if (not horoscope_object.groups()):
            return {}
        horoscopeUrl = re.match("<script>\s+window\.location\.href=\"(.+)\";</script>",horoscopeIntermediateResponse).group(1).replace("\\/","/")
        # append hk to horoscopeUrl
        #horoscopeUrl += '&hk=c4e65ee6f77e2297dbb2fd8fdd7f44cb'
        horoscopeResponse = MakeGetRequest(horoscopeUrl,TeluguMatrimonyCookies)
        if horoscopeResponse == None:
          return {}
        horoscopeDoc = BeautifulSoup(horoscopeResponse)
        if horoscopeDoc == None or horoscopeDoc.find("body") == None:
          return {}
        if(horoscopeDoc.find("body")["onload"] != None):
            horoscopeDetailsUrl = re.match('jqajaxRequest\(\'([^,]+)\',.+\)',horoscopeDoc.find("body")["onload"]).group(1)
            horoscopeDetailsResponse = MakeGetRequest(horoscopeDetailsUrl, TeluguMatrimonyCookies)
            if (horoscopeDetailsResponse == None or len(horoscopeDetailsResponse) == 0):
                return {}
            horoscopeDoc = BeautifulSoup(horoscopeDetailsResponse)
            horoscopeNodes = [node for node in horoscopeDoc.find_all("div",class_="smalltxt") if node.text.startswith("Name")]
            if(len(horoscopeNodes) > 0):
            	horoscopeNode = horoscopeNodes[0]
                horoscope = Sanitize(horoscopeNode.text)
                horoscopeDetails = dict([(key.split(':')[0].strip(),':'.join(key.split(':')[1:]).strip()) for key in horoscope.split('|')])
    # if the horoscope is empty request horoscope
    if((len(horoscopeDetails) == 0) and MakeHoroscopeRequestFromUser):
        horoscopeDetails = MakeHoroscopeRequest(TNo)
    return horoscopeDetails
    
def GetMatchScores(UserBirthPlaceDetails, ConfigParams, UserBirthDateTime, candidateName, candidateBirthDate, candidateBirthPlace, candidateBirthCountry, ayanamsa):
    global MatchScoresUrl
    matchScores = {};
    #Dictionary<string, string> birthPlaceDetails = GetPlaceDetails("INDIA", candidateBirthPlace);
    birthPlaceDetails = GetPlaceDetails_new("INDIA", candidateBirthPlace)
    if ((len(birthPlaceDetails.keys()) > 0) and (len(UserBirthPlaceDetails.keys()) > 0)):
        candidateCountry = birthPlaceDetails["Country"] if ("Country" in birthPlaceDetails) else None;
        candidateCity =  birthPlaceDetails["City"] if ("City" in birthPlaceDetails) else None;
        candidateLongitude = birthPlaceDetails["Longitude"] if ("Longitude" in birthPlaceDetails) else None;
        candidateLatitude =  birthPlaceDetails["Latitude"] if ("Latitude" in birthPlaceDetails) else  None;
        candidateTimeZone =  birthPlaceDetails["Time Zone"] if ("Time Zone" in birthPlaceDetails) else None;
        candidateNSDirection =  candidateLongitude[-1] if (candidateLongitude) else None;
        candidateEWDirection =  candidateLatitude[-1] if (candidateLatitude) else None;
        candidateLatitude =  candidateLatitude[:-2] if (len(candidateLatitude) > 2) else None;
        candidateLongitude =  candidateLongitude[:-2] if (len(candidateLongitude) > 2) else None;

        userCountry = UserBirthPlaceDetails["Country"] if ("Country" in UserBirthPlaceDetails) else None;
        userCity = UserBirthPlaceDetails["City"] if ("City" in UserBirthPlaceDetails) else None;
        userLongitude = UserBirthPlaceDetails["Longitude"] if ("Longitude" in UserBirthPlaceDetails) else None;
        userLatitude = UserBirthPlaceDetails["Latitude"] if ("Latitude" in UserBirthPlaceDetails) else None;
        userTimeZone = UserBirthPlaceDetails["Time Zone"] if ("Time Zone" in UserBirthPlaceDetails) else None;

        userNSDirection = userLongitude[-1] if (userLongitude) else None;
        userEWDirection = userLatitude[-1] if (userLatitude) else None;

        userLatitude = userLatitude[:-2] if (len(userLatitude) > 2) else None;
        userLongitude = userLongitude[:-2] if (len(userLongitude) > 2) else None;

        boyDetails = None
        girlDetails = None
        
        if ("Gender" in ConfigParams):
            if (ConfigParams["Gender"].lower()[0] == 'm'):
                boyDetails = MatchScoresBoyDetails.format(ConfigParams["Name"], UserBirthDateTime.day, UserBirthDateTime.month, UserBirthDateTime.year, UserBirthDateTime.hour, UserBirthDateTime.minute, userCountry, userCity, userLongitude, userEWDirection, userLatitude, userNSDirection, userTimeZone);
                girlDetails = MatchScoresGirlDetails.format(candidateName, candidateBirthDate.day, candidateBirthDate.month, candidateBirthDate.year, candidateBirthDate.hour, candidateBirthDate.minute, candidateCountry, candidateCity, candidateLongitude, candidateNSDirection, candidateLatitude, candidateEWDirection, candidateTimeZone);
            else:
                girlDetails = MatchScoresGirlDetails.format(ConfigParams["Name"], UserBirthDateTime.day, UserBirthDateTime.month, UserBirthDateTime.year, UserBirthDateTime.hour, UserBirthDateTime.minute, userCountry, userCity, userLongitude, userEWDirection, userLatitude, userNSDirection, userTimeZone);
                boyDetails = MatchScoresBoyDetails.format(candidateName, candidateBirthDate.day, candidateBirthDate.month, candidateBirthDate.year, candidateBirthDate.hour, candidateBirthDate.minute, candidateCountry, candidateCity, candidateLongitude, candidateNSDirection, candidateLatitude, candidateEWDirection, candidateTimeZone);

        matchScoresPost = MatchScoresPostRequestTemplate.format(boyDetails, girlDetails, (ayanamsa != "Chitra Paksha"));

        
        request = urllib2.Request(url=MatchScoresUrl,data=matchScoresPost)
        try:
            response = urllib2.urlopen(request)
        except urllib2.URLError:
            return matchScores
        if (response.getcode() == 200):
            doc = BeautifulSoup(response.read())
            scoresNodes = [node for node in doc.find(id="AutoNumber1").find_all("tr")[1:] if len(node.find_all("td")) == 5]
            for scoresNode in scoresNodes:
                 matchScores[Sanitize(scoresNode.find_all("td")[0].text)] = (Sanitize(scoresNode.find_all("td")[2].text), Sanitize(scoresNode.find_all("td")[4].text));
            totalScoreNode = doc.find(id="tscore1")
            matchScores["Total"] = ("Total", Sanitize(totalScoreNode.text))
    
    return matchScores

def GetPlaceDetails(countryName, cityName):
    placeInformation = {}
    if (cityName):
        try:
            placeResponse = MakePostRequest(PlaceFinderUrl, PlaceFinderPostTemplate.format(countryName, cityName), AskGaneshCookies)
            doc = BeautifulSoup(placeResponse)
            placeDetailsNode = doc.find(id="AutoNumber2")
            placeInformation=[(Sanitize(node.find_all("td")[0].text), Sanitize(node.find_all("td")[1].text)) for node in placeDetailsNode.find_all("tr") if len(node.find_all("td"))==2]
        except Exception:
            return placeInformation
    return placeInformation
    
def GetPlaceDetails_new(countryName, cityName):
    global GoogleGeoCoderApiUrl
    placeInformation = {}
    if(cityName):
        try:
            placeResponse = MakePostRequest(GoogleGeoCoderApiUrl.format(cityName, countryName), None, None)
            doc = xml.dom.minidom.parseString(placeResponse)
            resultNode = doc.getElementsByTagName('result')[0]
            # making the values compatible with the old values
            locationNode = doc.getElementsByTagName('result')[0].getElementsByTagName('geometry')[0].getElementsByTagName('location')[0]
            latitude = float(locationNode.getElementsByTagName('lat')[0].firstChild.nodeValue)
            placeInformation["Latitude"] = str(latitude)+".E" if (latitude >=0) else str(latitude)+".W"
            longitude = float(locationNode.getElementsByTagName('lng')[0].firstChild.nodeValue)
            placeInformation["Longitude"] = str(longitude) + ".N" if (longitude > 0) else (longitude) + ".S"
            
            placeInformation["City"] = [node for node in doc.getElementsByTagName("address_component") if node.getElementsByTagName("type")[0].firstChild.nodeValue == "locality"][0].getElementsByTagName("long_name")[0].firstChild.nodeValue
            placeInformation["Country"] = [node for node in doc.getElementsByTagName("address_component") if node.getElementsByTagName("type")[0].firstChild.nodeValue == "country"][0].getElementsByTagName("long_name")[0].firstChild.nodeValue
            placeInformation["Time Zone"] = "-5.5"
        except Exception:
            return placeInformation
    return placeInformation
    
def GetSearchTNos(ConfigParams):
    
    startCount = 1
    searchNext = True
    TNos = []
    while searchNext:
        searchPostRequestTemplate = ConfigParams["SearchQuery"] + SearchPostSuffixTemplate;
        try:
            profiles = MakePostRequest(SearchUrl, searchPostRequestTemplate.format(startCount), TeluguMatrimonyCookies)
            profiles = json.loads(profiles.split('~')[2])["profiles"]
            if(len(profiles) > 0):
                startCount += len(profiles)
                TNos.extend([profile["MId"] for profile in profiles])
            else:
                searchNext = False
        except Exception:
            continue
    return TNos
    
def MakeHoroscopeRequest(TNo):
    global RequestHoroscopeUrl
    global RequestHoroscopePostRequestTemplate
    postContent = RequestHoroscopePostRequestTemplate.format(TNo)
    response = MakePostRequest(RequestHoroscopeUrl, postContent, TeluguMatrimonyCookies)
    if "Horoscope Request Sent" in response:
        return True
    else:
        return False

def Sanitize(word):
    return re.sub("\s+", " ", HTMLParser.HTMLParser().unescape(word).replace("\t", "").replace("\n", "").replace("\r", "").strip());

def MakePostRequest(url, postContent, cookies):
    opener = build_opener(HTTPCookieProcessor(cookies), HTTPHandler())
    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
               "UserAgent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31",
               "ContentType": "application/x-www-form-urlencoded"}
    request = urllib2.Request(url=url,data=postContent,headers=headers)
    
    try:
        response = opener.open(request)
    except urllib2.URLError:
        return None
    return response.read()

def MakeGetRequest(url, cookies):
    opener = build_opener(HTTPCookieProcessor(cookies), HTTPHandler())
    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
               "UserAgent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31",
               "ContentType": "application/x-www-form-urlencoded"}
    request = urllib2.Request(url=url,headers=headers)
    try:
        response = opener.open(request)
    except urllib2.URLError:
        return None
    return response.read()
    
def GetProfileData(TNo, inputColumns, TeluguMatrimonyCookies, UserBirthPlaceDetails, ConfigParams, UserBirthDateTime):
    sys.stderr.write('Getting profile data for :' + TNo + '\n')
    candidateInfo = {}
    candidateHoroscope = {}
    matchScores = {}
    candidateInfo = GetUserDetails(TNo, TeluguMatrimonyCookies);
    column_count = 0
    if(inputColumns != None):
        column_count = len(inputColumns)
    # overriding the provided input details
    if ("Basic Details" not in candidateInfo):
        candidateInfo["Basic Details"] = {}
    if ("Religious Information" not in candidateInfo):
        candidateInfo["Religious Information"] = {}
    if ("Location" not in candidateInfo):
        candidateInfo["Location"] = {}      
    if (inputColumns and column_count > 1 and inputColumns[1]):
        candidateInfo["Basic Details"]["Name"] = inputColumns[1]
    if (inputColumns and column_count > 2 and inputColumns[2]):
        candidateInfo["Basic Details"]["Age"] = inputColumns[2];
    if (inputColumns and column_count > 3 and inputColumns[3]):
        candidateInfo["Basic Details"]["Height"] = inputColumns[3];
    if (inputColumns and column_count > 4 and inputColumns[4]):
        candidateInfo["Basic Details"]["Eating Habits"] = inputColumns[4];
    if (inputColumns and column_count > 5 and inputColumns[5]):
        candidateInfo["Religious Information"]["Caste / Sub Caste"] = inputColumns[5];
    if (inputColumns and column_count > 6 and inputColumns[6]):
        candidateInfo["Religious Information"]["Gothram"] = inputColumns[6];
    if (inputColumns and column_count > 7 and inputColumns[7]):
        candidateInfo["Religious Information"]["Star / Raasi"] = inputColumns[7];
    if (inputColumns and column_count > 8 and inputColumns[8]):
        candidateInfo["Religious Information"]["Kuja Dosham"] = inputColumns[8];
    if (inputColumns and column_count > 9 and inputColumns[9]):
        candidateInfo["Location"]["City"] = inputColumns[9];
    if (inputColumns and column_count > 10 and inputColumns[10]):
        candidateInfo["Location"]["State"] = inputColumns[10];
    if (inputColumns and column_count > 11 and inputColumns[11]):
        candidateInfo["Location"]["Country"] = inputColumns[11];
    # Getting the new Horoscope details
    candidateHoroscope = GetHoroscopeDetails(TNo, TeluguMatrimonyCookies);
    # If there are further details overriding them
    if (inputColumns and column_count > 12 and inputColumns[12]):
        candidateHoroscope["Date of Birth"] = inputColumns[12];
    if (inputColumns and column_count > 13 and inputColumns[13]):
        candidateHoroscope["Time of Birth (Hr.Min.Sec)"] = inputColumns[13];
    if (inputColumns and column_count > 14 and inputColumns[14]):
        candidateHoroscope["Time Zone (Hr.Min.Sec)"] = inputColumns[14];
    if (inputColumns and column_count > 15 and inputColumns[15]):
        candidateHoroscope["Place of Birth"] = inputColumns[15];
    matchScores = {}
    if (len(candidateHoroscope) > 0):
        candidateName = candidateHoroscope["Name"] if ("Name" in candidateHoroscope) else None
        if (("Date of Birth" in candidateHoroscope) and ("Time of Birth (Hr.Min.Sec)" in candidateHoroscope)):
            candidateBirthTimeString = candidateHoroscope["Date of Birth"].split(',')[0] + " " + candidateHoroscope["Time of Birth (Hr.Min.Sec)"].split(',')[0];
            candidateBirthTimeString = candidateBirthTimeString.replace("\"", "").strip();
            candidateBirthTime = datetime.datetime.strptime(candidateBirthTimeString,"%d %B %Y %I:%M:%S %p")
            candidateBirthPlace = candidateHoroscope["Place of Birth"].split('(')[0].strip() if ("Place of Birth" in candidateHoroscope) else None
            candidateCountry =  candidateInfo["Location"]["Country"] if (("Location" in candidateInfo) and ("Country" in candidateInfo["Location"])) else None
            ayanamsa = candidateHoroscope["Ayanamsa"]  if ("Ayanamsa" in candidateHoroscope) else None
            matchScores = GetMatchScores(UserBirthPlaceDetails, ConfigParams, UserBirthDateTime, candidateName, candidateBirthTime, candidateBirthPlace, candidateCountry, ayanamsa)
    sys.stderr.write('Finished Getting profile data for :' + TNo + '\n')
    return (candidateInfo,candidateHoroscope, matchScores)

def PrintOutputLine(TNo, candidateInfo, candidateHoroscope, matchScores):
    global OutputFile
    outputColumns = [
                        TNo,
                        candidateInfo["Basic Details"]["Name"] if ("Basic Details" in candidateInfo) and ("Name" in candidateInfo["Basic Details"]) else "",
                        candidateInfo["Basic Details"]["Age"] if ("Basic Details" in candidateInfo) and ("Age" in candidateInfo["Basic Details"]) else "",
                        candidateInfo["Basic Details"]["Height"] if ("Basic Details" in candidateInfo) and ("Height" in candidateInfo["Basic Details"]) else "",
                        candidateInfo["Basic Details"]["Eating Habits"] if ("Basic Details" in candidateInfo) and ("Eating Habits" in candidateInfo["Basic Details"]) else "",
                        candidateInfo["Religious Information"]["Caste / Sub Caste"] if ("Religious Information" in candidateInfo) and ("Caste / Sub Caste" in candidateInfo["Religious Information"]) else "",
                        candidateInfo["Religious Information"]["Gothram"] if ("Religious Information" in candidateInfo) and ("Gothram" in candidateInfo["Religious Information"]) else "",
                        candidateInfo["Religious Information"]["Star / Raasi"] if ("Religious Information" in candidateInfo) and ("Star / Raasi" in candidateInfo["Religious Information"]) else "",
                        candidateInfo["Religious Information"]["Kuja Dosham"] if ("Religious Information" in candidateInfo) and ("Kuja Dosham" in candidateInfo["Religious Information"]) else "",
                        candidateInfo["Location"]["City"] if ("Location" in candidateInfo) and ("City" in candidateInfo["Location"]) else "",
                        candidateInfo["Location"]["State"] if ("Location" in candidateInfo) and ("State" in candidateInfo["Location"]) else "",
                        candidateInfo["Location"]["Country"] if ("Location" in candidateInfo) and ("Country" in candidateInfo["Location"]) else "",
                        candidateHoroscope["Date of Birth"] if "Date of Birth" in candidateHoroscope else "",
                        candidateHoroscope["Time of Birth (Hr.Min.Sec)"] if "Time of Birth (Hr.Min.Sec)" in candidateHoroscope else "",
                        candidateHoroscope["Time Zone (Hrs.Mins)"] if "Time Zone (Hrs.Mins)" in candidateHoroscope else "",
                        candidateHoroscope["Place of Birth"] if "Place of Birth" in candidateHoroscope else "",
                        matchScores["Varna (For work)"][1] if "Varna (For work)" in matchScores else "",
                        matchScores["Vashya (Personal relations)"][1] if "Vashya (Personal relations)" in matchScores else "",
                        matchScores["Tara (For destiny)"][1] if "Tara (For destiny)" in matchScores else "",
                        matchScores["Yoni (For metal compatibility)"][1] if "Yoni (For metal compatibility)" in matchScores else "",
                        matchScores["Graha (For nature)"][1] if "Graha (For nature)" in matchScores else "",
                        matchScores["Gan (For social relations)"][1] if "Gan (For social relations)" in matchScores else "",
                        matchScores["Bhakut (For life)"][1] if "Bhakut (For life)" in matchScores else "",
                        matchScores["Nadi (For physical compatibly)"][1] if "Nadi (For physical compatibly)" in matchScores else "",            
                        matchScores["Total"][1] if "Total" in matchScores else "",
                    ]
    outputLine = ("\t".join(outputColumns)+"\n").encode("utf-8", 'replace')
    if (OutputFile):
        OutputFile.write(outputLine)
    else:
        sys.stdout.write(outputLine)
    
class myThread (threading.Thread):
    
    def __init__(self, threadID, threadName, TNo, inputColumns, TeluguMatrimonyCookies, UserBirthPlaceDetails, ConfigParams, UserBirthDateTime):
        threading.Thread.__init__(self)
        #local_TNo = copy.deepcopy(TNo)
        #local_inputColumns = copy.deepcopy(inputColumns)
        self.threadID = threadID
        self.name = threadName
        self.TNo = TNo
        self.inputColumns = inputColumns
        self.TeluguMatrimonyCookies = TeluguMatrimonyCookies
        self.UserBirthPlaceDetails = UserBirthPlaceDetails
        self.ConfigParams = ConfigParams
        self.UserBirthDateTime = UserBirthDateTime
        
    def run(self):
        (candidateInfo, candidateHoroscope, matchScores) = GetProfileData(self.TNo, self.inputColumns, self.TeluguMatrimonyCookies, self.UserBirthPlaceDetails, self.ConfigParams, self.UserBirthDateTime)
        PrintOutputLine(self.TNo, candidateInfo, candidateHoroscope, matchScores)
        
class wrapperThreadWithTimeOut(threading.Thread):
    global threadExecTime
    
    def __init__(self, threadID, threadName, TNo, inputColumns, TeluguMatrimonyCookies, UserBirthPlaceDetails, ConfigParams, UserBirthDateTime):
        threading.Thread.__init__(self)
        #local_TNo = copy.deepcopy(TNo)
        #local_inputColumns = copy.deepcopy(inputColumns)
        self.threadID = "w"+str(threadID)
        self.name = "wrapper_"+threadName
        self.TNo = TNo
        self.TeluguMatrimonyCookies = TeluguMatrimonyCookies
        self.UserBirthPlaceDetails = UserBirthPlaceDetails
        self.ConfigParams = ConfigParams
        self.UserBirthDateTime = UserBirthDateTime
        self.inputColumns = inputColumns
    def run(self):
        # make deep copies of data
        thread = myThread(self.threadID,self.name,self.TNo, self.inputColumns, self.TeluguMatrimonyCookies, self.UserBirthPlaceDetails, self.ConfigParams, self.UserBirthDateTime)
        thread.start()
        thread.join(threadExecTime)    
    
if __name__ == "__main__":
    
    # Parsing command line arguments
    (MissFilling, ConfigFileName, InputTsvFileName, OutputFile) = ParseCommandLineParams(sys.argv, Usage)
    
    (ConfigParams,UserBirthPlaceDetails, UserBirthDateTime) = ReadConfig(ConfigFileName)
    
    # getting the login cookies
    if(("TNo" in ConfigParams) & ("Password" in ConfigParams)):
        GetTeluguMatrimonyLoginCookies(ConfigParams["TNo"], ConfigParams["Password"], TeluguMatrimonyCookies, LoginUrl)
        
    candidateInfo = {}
    candidateHoroscope = {}
    matchScores = {}
    
    i = 0
    if MissFilling:
        # Fill Missing Mode #
        
        # reading input file
        fileHandler = open(InputTsvFileName, "r")
        first = True
        for line in fileHandler:
            inputColumns = line.strip().split('\t')
            
            if line.startswith("TNo") & first:
                OutputHeaders = inputColumns
                continue
                
            if first:
                if (OutputFile):
                    OutputFile.write("\t".join(OutputHeaders) + "\n")
                else:
                    sys.stdout.write("\t".join(OutputHeaders) + "\n")
                first = False
            
            # parsing the columns
            TNo = inputColumns[0]
            if(threading.activeCount() > threadMaxCount):
                # wait until the count becomes upto min count
                while(threading.activeCount() > threadMinCount):
                    time.sleep(threadPollWait)
            # adding the further threads
            thread = wrapperThreadWithTimeOut(i,"thread"+TNo,TNo, inputColumns, TeluguMatrimonyCookies, UserBirthPlaceDetails, ConfigParams, UserBirthDateTime)
            thread.start()
            i +=1
            #(candidateInfo, candidateHoroscope, matchScores) = GetProfileData(TNo, inputColumns)
            #PrintOutputLine(TNo, candidateInfo, candidateHoroscope, matchScores)
    else:
        # Writing The header
        if (OutputFile):
            OutputFile.write("\t".join(OutputHeaders) + "\n")
        else:
            sys.stdout.write("\t".join(OutputHeaders) + "\n")
        
        # Scrape from start #
        
        # getting the search results (Tnos)
        TNos = GetSearchTNos(ConfigParams)
        # Getting the profile data for each TNo
        for TNo in TNos:
            if(threading.activeCount() > (2*threadMaxCount)):
                # wait until the count becomes upto min count
                # each will span two threads
                while(threading.activeCount() > (2*threadMinCount)):
                    time.sleep(threadPollWait)
            # adding the further threads
            thread = wrapperThreadWithTimeOut(i,"thread"+TNo,TNo, None, TeluguMatrimonyCookies, UserBirthPlaceDetails, ConfigParams, UserBirthDateTime)
            thread.start()
            i +=1
    
    # wait for all threads to exit. current thread accounts for 1 thread
    sys.stderr.write("Waiting for remaining threads to exit ..\n")
    waitTime = 0;
    while(threading.activeCount() > 1):
        #sys.stderr.write("active thread count:" + str(threading.activeCount()) + "\n")
        time.sleep(threadPollWait)
        waitTime += threadPollWait
        # if wait time is really high, one of the threads is struck so kill. using 15 mins as limit
        if waitTime > (15*60):
            break
    
    #### End of main program ####
