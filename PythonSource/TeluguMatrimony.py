import datetime
import sys
import urllib
import urllib2
import xml.dom.minidom
import re
import HTMLParser
from bs4 import BeautifulSoup
############################################################################################################################################
######################################################## Global Variables ##################################################################
############################################################################################################################################


Usage = "TeluguMatrimonyScrapper.exe <config file> \n OR \n TeluguMatrimonyScrapper.exe -FillMissing <config file> <tsv file>";
ConfigFileName;
InputTsvFileName;
MissFilling = False;

private static Regex TNoRegex = new Regex("\\((T\\d+)\\)", RegexOptions.Compiled);
private static Regex searchTNoListRegex = new Regex("\"perpage_ids\"\\s*:\\s*\"([T\\d,]+)\"", RegexOptions.Compiled);

# telugu matrimony urls
HoroscopeUrlTemplate = "http://image.telugumatrimony.com/horoscopegen/{0}/{1}/MHENG{2}.html";
SearchUrl = "http://profile.telugumatrimony.com/search/fetchrsearchresult.php";
ProfileUrlTemplate = "http://profile.telugumatrimony.com/profiledetail/viewprofile.php?id={0}";
LoginUrl = "https://secure.telugumatrimony.com/login/memlogin.php";

# THE TEMPLATE IS VERY SPECIFIC TO A USER.
SearchPostSuffixTemplate = "&PHOTO_OPT=N&HOROSCOPE_OPT=N&IGNORE_OPT=N&CONTACT_OPT=N&VIEW_OPT=N&SHORTLIST_OPT=N&DISPLAY_FORMAT=six&randid=a917993s&but_save=&SEARCH_TYPE=ADVANCESEARCH&SEARCH_ID=Mg==&ss=&wherefrom=frmpaging&facet=N&STLIMIT={0}";
private static CookieContainer TeluguMatrimonyCookies = new CookieContainer();
private static CookieContainer AskGaneshCookies = new CookieContainer();

MatchScoresUrl = "http://askganesa.com/services/free_horoscope/gun-milan-new1.aspx";
MatchScoresBoyDetails = "bname={0}&bdate={1}&bmonth={2}&byear={3}&bhour={4}&bmin={5}&bcountry={6}&bcity={7}&longitude={8}&ew={9}&latitude={10}&ns={11}&timediff={12}";
MatchScoresGirlDetails ="gname={0}&gdate={1}&gmonth={2}&gyear={3}&ghour={4}&gmin={5}&gcountry={6}&gcity={7}&glongitude={8}&gns={9}&glatitude={10}&gew={11}&gtimediff={12}";
MatchScoresPostRequestTemplate = "{0}&{1}&ayanamsa={2}&terms=0&B1=Submit";

PlaceFinderUrl = "http://askganesha.com/hindi/place_finder.asp?act=find ";
PlaceFinderPostTemplate = "country={0}&city={1}&B1=Submit";

GoogleGeoCoderApiUrl = "https://maps.googleapis.com/maps/api/geocode/xml?address={0},%20{1}&sensor=false&key=AIzaSyD-WrDl5VHXznx7cG-gRWsDCNpa0cKqG2Y";

outputHeader = ["TNo", "Name","Age","Height","Eating Habits","Caste / Sub Caste","Gothram","Star / Raasi","Kuja Dosham","City","State","Country","Date of Birth","Time of Birth","Time Zone","Place of Birth","Varna","Vashya","Tara","Yoni","Graha","Gan","Bhakut","Nadi","Total Score"]

############################################################################################################################################
##################################################### End of Global Variables ##############################################################
############################################################################################################################################

ConfigParams ={};
UserBirthPlaceDetails = {};
UserBirthDateTime;

def ParseCommandLineParams(args):
    if args.length == 0:
        raise Exception(Usage)
        
    if args[0].lower == "-fillmissing":
        if args.length < 3:
            raise Exception(Usage)
        ConfigFileName = args[1]
        InputTsvFileName = args[2]
        MissFilling = True
    else:
        ConfigFileName = args[0]

def ReadConfig(fileName):
    configParams = {}
    fileHandler = open(fileName, "r")
    for line in fileHandler:
        if !line.startwith(";"):
            cols = line.split('=')
            if cols.length >= 2:
                configParams[cols[0]] = cols[1:].join('=')
            
    # checking for all the requried values being present in the config file
    if (! "TNo" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"TNo\". (the parameter names are case sensitive)")
    
    if (! "Password" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"Password\". (the parameter names are case sensitive)")
    
    if (! "SearchQuery" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"SearchQuery\". (the parameter names are case sensitive)")
    
    if (! "Name" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"Name\". (the parameter names are case sensitive)")
    
    if (! "Gender" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"Gender\". (the parameter names are case sensitive)")
    
    if (! "DateOfBirth" in configParams):
        raise KeyNotFoundException("The config file doesn't contain the parameter \"DateOfBirth\". (the parameter names are case sensitive)")
    
    if (! "TimeOfBirth" in configParams)
        raise KeyNotFoundException("The config file doesn't contain the parameter \"TimeOfBirth\". (the parameter names are case sensitive)")
                
    if (! "CountryOfBirth" in configParams)
        raise KeyNotFoundException("The config file doesn't contain the parameter \"CountryOfBirth\". (the parameter names are case sensitive)")
                
    if (! "CityOfBirth" in configParams)
        raise KeyNotFoundException("The config file doesn't contain the parameter \"CityOfBirth\". (the parameter names are case sensitive)")
                

    # Get user birth details
    #UserBirthPlaceDetails = GetPlaceDetails(configParams["CountryOfBirth"], configParams["CityOfBirth"]);
    UserBirthPlaceDetails = GetPlaceDetails_new(configParams["CountryOfBirth"], configParams["CityOfBirth"])
    
    try:
        UserBirthDateTime = datetime.datetime.strptime(configParams["DateOfBirth"] + " " + configParams["TimeOfBirth"])
        break
    except ValueError:
        sys.stderr.write("Error parsing the User Date of Birth and Time of birth. Ignoring the data")
    
    return configParams

def GetTeluguMatrimonyLoginCookies(tNo, password):
    postContent = "ID={0}&PASSWORD={1}".format(tNo, password)
    #### REMOVE THIS #####
    #MakePostRequest(LoginUrl, postContent);

def GetAskGaneshCookies():
    #### REMOVE THIS ##
    #MakePostRequest("http://www.askganesha.com/services/free_horoscope/gun-milan.asp", "", AskGaneshCookies)

def GetUserProfile(TNo):
    profileUrl = ProfileUrlTemplate.format(TNo)
    
    ### REMOVE THIS ###
    #request.CookieContainer = TeluguMatrimonyCookies;
    request = urllib2.Request(profileUrl)
    try:
        response = urllib2.urlopen(request)
        if response.getcode() != 200:
            return response.read()
    except urllib2.URLError:
        
    return None
    
def GetUserDetails(TNo):
    userInfo = {}
    htmlDoc
    userProfile = GetUserProfile(TNo)
    
    if userProfile != None:
        htmlDoc = BeautifulSoup(userProfile)

    try:
        # Getting Details
        detailsNode = htmlDoc.find(id="vp-details")
        parentInfoNode = detailsNode.find_all("div",class_="fleft")[0].parent
        
        # converting the information into a dictionary
        sectionHeader = "";
        prefix = "";
        for infoNode in parentInfoNode.find_all("div"):
            # check for main headers
            if (len(infoNode["class"]) > 0 && "boldtxt" in infoNode["class"] && "biggertxt" in infoNode["class"]):
                prefix = Sanitize(infoNode.text);
            
            # check for section headers div
            if (len(infoNode["class"]) > 0 && "boldtxt" in infoNode["class"] && "bigtxt" in infoNode["class"]):
                sectionHeader = Sanitize(infoNode.text);
                userInfo[prefix + "_" + sectionHeader] = {};
            
            elif (len(infoNode["class"]) > 0 && "fleft" in infoNode["class"]):
                subNodes = infoNode.find_all("div", class_="fleft")
                if (len(subNodes) >= 2):
                    int i = 0;
                    while (i < len(subNodes)):
                        userInfo[prefix + "_" + sectionHeader][Sanitize(subNodes[i].text)] = Sanitize(subNodes[i + 1].text);
                        i += 2;
                
    except Exception:
        
    return userInfo
    
def GetHoroscopeDetails(TNo):
    horoscopeDetails = {};
    horoscopeUrl = HoroscopeUrlTemplate.format(TNo[1], TNo[2], TNo);

    request = urllib2.Request(horoscopeUrl);
    try:
        response = urllib2.urlopen(request)
        if (response.getcode() == 200):
            horoscopeDoc = BeautifulSoup(response.read())
            horoscopeNode = [node for node in horoscopeDoc.find_all("div",class_="smalltxt") if node.text.startswith("Name")][0]
            string horoscope = Sanitize(horoscopeNode.text);
            horoscopeDetails = dict([(key.split(':')[0].strip(),key.split(':')[1:].join(':').strip()) for key in horoscope.split('|')])
    except urllib2.URLError:
        
    return horoscopeDetails
    
def GetMatchScores(candidateName, candidateBirthDate, candidateBirthPlace, candidateBirthCountry, ayanamsa):
    matchScores = {};
    #Dictionary<string, string> birthPlaceDetails = GetPlaceDetails("INDIA", candidateBirthPlace);
    birthPlaceDetails = GetPlaceDetails_new("INDIA", candidateBirthPlace)
    if (len(birthPlaceDetails.keys()) > 0 && len(UserBirthPlaceDetails.keys) > 0):
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

        string boyDetails, girlDetails;

        if (ConfigParams["Gender"].lower()[0] == 'm'):
            boyDetails = MatchScoresBoyDetails.format(ConfigParams["Name"], UserBirthDateTime.Day, UserBirthDateTime.Month, UserBirthDateTime.Year, UserBirthDateTime.Hour, UserBirthDateTime.Minute, userCountry, userCity, userLongitude, userEWDirection, userLatitude, userNSDirection, userTimeZone);
            girlDetails = MatchScoresGirlDetails.format(candidateName, candidateBirthDate.Day, candidateBirthDate.Month, candidateBirthDate.Year, candidateBirthDate.Hour, candidateBirthDate.Minute, candidateCountry, candidateCity, candidateLongitude, candidateNSDirection, candidateLatitude, candidateEWDirection, candidateTimeZone);
        else:
            girlDetails = MatchScoresGirlDetails.format(ConfigParams["Name"], UserBirthDateTime.Day, UserBirthDateTime.Month, UserBirthDateTime.Year, UserBirthDateTime.Hour, UserBirthDateTime.Minute, userCountry, userCity, userLongitude, userEWDirection, userLatitude, userNSDirection, userTimeZone);
            boyDetails = MatchScoresBoyDetails.format(candidateName, candidateBirthDate.Day, candidateBirthDate.Month, candidateBirthDate.Year, candidateBirthDate.Hour, candidateBirthDate.Minute, candidateCountry, candidateCity, candidateLongitude, candidateNSDirection, candidateLatitude, candidateEWDirection, candidateTimeZone);

        matchScoresPost = MatchScoresPostRequestTemplate.format(boyDetails, girlDetails, (ayanamsa != "Chitra Paksha"));

        try:
            request = urllib2.Request(url=MatchScoresUrl,data=matchScoresPost)
            try:
                response = urllib2.urlopen(request)
            except urllib2.URLError:
            
            if (response.getcode() == 200):
                doc = BeautifulSoup(response.read())
                scoresNodes = [node for node in doc.find(id="AutoNumber1").find_all("tr")[1:] if len(node.find_all("td")) == 5]
                for scoresNode in scoresNodes:
                     matchScores[Sanitize(node.find_all("td")[0].text)] = (Sanitize(node.find_all("td")[2].text), Sanitize(node.find_all("td")[4].text));
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
    
def GetPlaceDetails_new(countryName, cityName):
    placeInformation = {}
    if(cityName):
        try:
            placeResponse = MakePostRequest(GoogleGeoCoderApiUrl.format(cityName, countryName), None)
            doc = xml.dom.mindom.parseString(placeResponse)
            resultNode = doc.getElementsByTagName('result')[0]
            # making the values compatible with the old values
            locationNode = dom.getElementsByTagName('result')[0].getElementsByTagName('geometry')[0].getElementsByTagName('location')[0]
            
            latitude = float(locationNode.getElementsByTagName('lat')[0].firstChild.nodeValue)
            placeInformation["Latitude"] = str(latitude)+".E" if (latitude >=0) else str(latitude)+".W"
            longitude = float(locationNode.getElementsByTagName('lng')[0].firstChild.nodeValue)
            placeInformation["Longitude"] = str(longitude) + ".N" if (longitude > 0) else (longitude) + ".S"
            
            placeInformation["City"] = [node for node in dom.getElementsByTagName("address_component") if node.getElementsByTagName("type")[0].firstChild.nodeValue == "locality"][0].getElementsByTagName("long_name")[0].firstChild.nodeValue
            placeInformation["Country"] = [node for node in dom.getElementsByTagName("address_component") if node.getElementsByTagName("type")[0].firstChild.nodeValue == "country"][0].getElementsByTagName("long_name")[0].firstChild.nodeValue
            placeInformation["Time Zone"] = "-5.5"
            
        except Exception:
            
    return placeInformation
    
def GetSearchTNos():
    startCount = 1
    searchNext = True
    TNos = []
    while searchNext:
        searchPostRequestTemplate = ConfigParams["SearchQuery"] + SearchPostSuffixTemplate;
        try:
            profiles = MakePostRequest(SearchUrl, searchPostRequestTemplate.format(startCount))
            profiles = profiles.Split('~')[2]
            matches = searchTNoListRegex.match(profiles)
            if len(match.groups()):
                profilesListString = match.group(1)
                profilesList = profilesListString.split(',')
                startCount += len(profilesList)
                TNos.extend(profilesList)
            else:
                searchNext = False
        except Exception:
            
    return TNos

def Sanitize(word):
    return re.sub(HTMLParser.HTMLParser().unescape(word).replace("\t", "").replace("\n", "").replace("\r", "").strip(), "\s+", " ");

def MakePostRequest(url, postContent):
    return MakePostRequest(url, postContent, TeluguMatrimonyCookies);

def MakePostRequest(url, postContent, cookies):
    headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", 
               "UserAgent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31",
               "ContentType": "application/x-www-form-urlencoded"}
    headers["Cookie"] = cookies;
    request = urllib2.Request(url=url,data=postContent,headers=headers)
    
    try:
        response = urllib2.urlopen(request)
        if(!cookies):
            cookies += response.info().getheader("Cookie")
    except urllib2.URLError:
        
    return response.read()
    
def GetProfileData(string TNo, string[] inputColumns, out Dictionary<string, Dictionary<string, string>> candidateInfo, out Dictionary<string, string> candidateHoroscope, out Dictionary<string, Tuple<string, string>> matchScores)
{
    candidateInfo = GetUserDetails(TNo);

    // overriding the provided input details
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[1]))
    {
        candidateInfo["Personal Information_Basic Details"]["Name"] = inputColumns[1];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[2]))
    {
        candidateInfo["Personal Information_Basic Details"]["Age"] = inputColumns[2];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[3]))
    {
        candidateInfo["Personal Information_Basic Details"]["Height"] = inputColumns[3];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[4]))
    {
        candidateInfo["Personal Information_Basic Details"]["Eating Habits"] = inputColumns[4];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[5]))
    {
        candidateInfo["Personal Information_Religious Information"]["Caste / Sub Caste"] = inputColumns[5];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[6]))
    {
        candidateInfo["Personal Information_Religious Information"]["Gothram"] = inputColumns[6];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[7]))
    {
        candidateInfo["Personal Information_Religious Information"]["Star / Raasi"] = inputColumns[7];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[8]))
    {
        candidateInfo["Personal Information_Religious Information"]["Kuja Dosham"] = inputColumns[8];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[9]))
    {
        candidateInfo["Personal Information_Location"]["City"] = inputColumns[9];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[10]))
    {
        candidateInfo["Personal Information_Location"]["State"] = inputColumns[10];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[11]))
    {
        candidateInfo["Personal Information_Location"]["Country"] = inputColumns[11];
    }
    // Getting the new Horoscope details

    candidateHoroscope = GetHoroscopeDetails(TNo);
    // If there are further details overriding them
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[12]))
    {
        candidateHoroscope["Date of Birth"] = inputColumns[12];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[13]))
    {
        candidateHoroscope["Time of Birth (Hr.Min.Sec)"] = inputColumns[13];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[14]))
    {
        candidateHoroscope["Time Zone (Hr.Min.Sec)"] = inputColumns[14];
    }
    if (inputColumns != null && !string.IsNullOrWhiteSpace(inputColumns[15]))
    {
        candidateHoroscope["Place of Birth"] = inputColumns[15];
    }

    matchScores = new Dictionary<string, Tuple<string, string>>();

    if (candidateHoroscope.Count > 0)
    {
        string candidateName = (candidateHoroscope.ContainsKey("Name")) ? candidateHoroscope["Name"] : String.Empty;
        if (candidateHoroscope.ContainsKey("Date of Birth") && candidateHoroscope.ContainsKey("Time of Birth (Hr.Min.Sec)"))
        {
            string candidateBirthTimeString = candidateHoroscope["Date of Birth"].Split(',')[0] + " " + candidateHoroscope["Time of Birth (Hr.Min.Sec)"].Split(',')[0];
            candidateBirthTimeString = candidateBirthTimeString.Replace("\"", "");
            DateTime candidateBirthTime = DateTime.Parse(candidateBirthTimeString);
            string candidateBirthPlace = (candidateHoroscope.ContainsKey("Place of Birth")) ? candidateHoroscope["Place of Birth"].Split('(')[0].Trim() : String.Empty;
            string candidateCountry = (candidateInfo.ContainsKey("Personal Information_Location") && candidateInfo["Personal Information_Location"].ContainsKey("Country")) ? candidateInfo["Personal Information_Location"]["Country"] : string.Empty;
            string ayanamsa = (candidateHoroscope.ContainsKey("Ayanamsa")) ? candidateHoroscope["Ayanamsa"] : String.Empty;
            matchScores = GetMatchScores(candidateName, candidateBirthTime, candidateBirthPlace, candidateCountry, ayanamsa);
        }
    }
}
