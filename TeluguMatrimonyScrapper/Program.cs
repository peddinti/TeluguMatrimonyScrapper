using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.IO;
using System.Net;
using System.Web;
using System.Threading.Tasks;
using HtmlAgilityPack;

namespace TeluguMatrimonyScrapper
{
    class Program
    {
        private const string Usage = "TeluguMatrimonyScrapper.exe -Config=<config file> -Output=<output tsv file>\n OR \nTeluguMatrimonyScrapper.exe [-FillMissing|-Update|-UpdateOnly] -Config=<config file> -Input=<Input tsv file> -Output=<output tsv file>";
        
        private static Regex TNoRegex = new Regex("\\((T\\d+)\\)", RegexOptions.Compiled);
        private static Regex searchTNoListRegex = new Regex("\"perpage_ids\"\\s*:\\s*\"([T\\d,]+)\"", RegexOptions.Compiled);

        // telugu matrimony urls
        private const string HoroscopeUrlTemplate = "http://image.telugumatrimony.com/horoscopegen/{0}/{1}/MHENG{2}.html";
        private const string SearchUrl = "http://profile.telugumatrimony.com/search/fetchrsearchresult.php";
        private const string ProfileUrlTemplate = "http://profile.telugumatrimony.com/profiledetail/viewprofile.php?id={0}";
        private const string LoginUrl = "https://secure.telugumatrimony.com/login/memlogin.php";

        // THE TEMPLATE IS VERY SPECIFIC TO A USER.
        private const string SearchPostSuffixTemplate = "&PHOTO_OPT=N&HOROSCOPE_OPT=N&IGNORE_OPT=N&CONTACT_OPT=N&VIEW_OPT=N&SHORTLIST_OPT=N&DISPLAY_FORMAT=six&randid=a917993s&but_save=&SEARCH_TYPE=ADVANCESEARCH&SEARCH_ID=Mg==&ss=&wherefrom=frmpaging&facet=N&STLIMIT={0}";
        private static CookieContainer TeluguMatrimonyCookies = new CookieContainer();

        private const string MatchScoresUrl = "http://askganesa.com/services/free_horoscope/gun-milan-new1.aspx";
        private const string MatchScoresBoyDetails = "bname={0}&bdate={1}&bmonth={2}&byear={3}&bhour={4}&bmin={5}&bcountry={6}&bcity={7}&longitude={8}&ew={9}&latitude={10}&ns={1}&timediff={12}";
        private const string MatchScoresGirlDetails ="gname={0}&gdate={1}&gmonth={2}&gyear={3}&ghour={4}&gmin={5}&gcountry={6}&gcity={7}&glongitude={8}&gns={9}&glatitude={10}&gew={11}&gtimediff={12}";
        private const string MatchScoresPostRequestTemplate = "{0}&{1}&ayanamsa={2}&terms=0&B1=Submit";
        
        private const string PlaceFinderUrl = "http://askganesa.com/services/free_horoscope/gplace_finder.asp?act=find ";
        private const string PlaceFinderPostTemplate = "country={0}&city={1}&B1=Submit";

        private static string[] OutputHeaders = new string[] {  "TNo",
                                                                "Name",
                                                                "Age",
                                                                "Height",
                                                                "Eating Habits",
                                                                "Caste / Sub Caste",
                                                                "Gothram",
                                                                "Star / Raasi",
                                                                "Kuja Dosham",
                                                                "City",
                                                                "State",
                                                                "Country",
                                                                "Date of Birth",
                                                                "Time of Birth",
                                                                "Time Zone",
                                                                "Place of Birth",
                                                                "Varna",
                                                                "Vashya",
                                                                "Tara",
                                                                "Yoni",
                                                                "Graha",
                                                                "Gan",
                                                                "Bhakut",
                                                                "Nadi",
                                                                "Total Score",
                                                                            };

        private static Dictionary<string, string> CommandLineParms = new Dictionary<string, string>();
        private static Dictionary<string, string> ConfigParams = new Dictionary<string, string>();
        private static Dictionary<string, string> UserBirthPlaceDetails = new Dictionary<string, string>();
        private static DateTime UserBirthDateTime;
        
        static void Main(string[] args)
        {
            if (!ParseCommandLineParams(args))
            {
                return;
            }
            
            // reading the input config file
            ConfigParams = ReadConfig(CommandLineParms["config"]);

            // login the user.
            if (ConfigParams.ContainsKey("TNo") && ConfigParams.ContainsKey("Password"))
            {
                GetTeluguMatrimonyLoginCookies(ConfigParams["TNo"], ConfigParams["Password"]);
            }

            // writing the header
            Console.WriteLine(string.Join("\t", OutputHeaders));

            Dictionary<string, Dictionary<string, string>> candidateInfo = new Dictionary<string, Dictionary<string, string>>();
            Dictionary<string, string> candidateHoroscope = new Dictionary<string, string>();
            Dictionary<string, Tuple<string, string>> matchScores = new Dictionary<string, Tuple<string, string>>();
            List<string> ExistingTNos = new List<string>();

            bool fillMissing = CommandLineParms.ContainsKey("fillmissing") && CommandLineParms["fillmissing"] == "true";
            bool update = CommandLineParms.ContainsKey("update") && CommandLineParms["update"] == "true";
            bool updateOnly = CommandLineParms.ContainsKey("updateonly") && CommandLineParms["updateonly"] == "true";
                        
            // If it is Fill missing values mode, search is not performed
            if (fillMissing||update||updateOnly)
            {
                // Reading from the input file
                using (StreamReader inputReader = new StreamReader(CommandLineParms["input"]))
                {
                    string line;
                    // skipping the first line as it contains the header
                    inputReader.ReadLine();
                    while ((line = inputReader.ReadLine()) != null)
                    {
                        string[] inputColumns = line.Split('\t');
                        // parsing the columns
                        if (inputColumns.Length != OutputHeaders.Length)
                        {
                            Console.Error.WriteLine(String.Format("Input line has invalid columns : {0}", line));
                        }
                        string TNo = inputColumns[0];
                        ExistingTNos.Add(TNo);
                        if (fillMissing)
                        {
                            GetProfileData(TNo, inputColumns, out candidateInfo, out candidateHoroscope, out matchScores);
                            PrintOutputLine(TNo, candidateInfo, candidateHoroscope, matchScores);
                        }
                        if (update && !updateOnly)
                        {
                            PrintOutputLine(line.Trim('\n').Trim('\r'));
                        }
                        
                    }
                }
            }
            if(!fillMissing)
            {
                // Getting all the Tno's to scrape based on search
                IEnumerable<string> TNos = GetSearchTNos();
                foreach (string TNo in TNos)
                {
                    if (!ExistingTNos.Contains(TNo))
                    {
                        GetProfileData(TNo, null, out candidateInfo, out candidateHoroscope, out matchScores);
                        PrintOutputLine(TNo, candidateInfo, candidateHoroscope, matchScores);
                    }
                }
            }
        }

        private static bool ParseCommandLineParams(string[] args)
        {
            if (args.Length == 0)
            {
                Console.Error.WriteLine(Usage);
                return false;
            }
            foreach (string arg in args)
            {
                if(!arg.StartsWith("-"))
                {
                    Console.Error.WriteLine("Invalid parameter " + arg);
                    Console.Error.WriteLine(Usage);
                    return false;
                }
                else if (arg.Contains("="))
                {
                    CommandLineParms[arg.Replace("-","").Split('=')[0].ToLower()] = arg.Replace("-","").Split('=')[1];
                }
                else
                {
                    CommandLineParms[arg.Replace("-", "").ToLower()] = "true";
                }
            }

            if (CommandLineParms.ContainsKey("fillmissing") || CommandLineParms.ContainsKey("update"))
            {
                if (!CommandLineParms.ContainsKey("input"))
                {
                    Console.Error.WriteLine("Missing parameter input");
                    Console.Error.WriteLine(Usage);
                    return false;
                }
            }
            if (!CommandLineParms.ContainsKey("config"))
            {
                Console.Error.WriteLine("Missing parameter config");
                Console.Error.WriteLine(Usage);
                return false;
            }
            return true;
        }

        /// <summary>
        /// reads the required parameters from the config file
        /// </summary>
        /// <param name="fileName">config file name</param>
        private static Dictionary<string,string> ReadConfig(string fileName)
        {
            Dictionary<string,string> configParams = new Dictionary<string,string>();
            using (StreamReader input = new StreamReader(fileName))
            {
                string line;
                while ((line = input.ReadLine()) != null)
                {
                    if (!line.StartsWith(";"))
                    {
                        string[] cols = line.Split('=');
                        if (cols.Length >= 2)
                        {
                            configParams[cols[0]] = string.Join("=",cols.Skip(1));
                        }
                    }
                }
            }

            // checking for all the requried values being present in the config file
            if (!configParams.ContainsKey("TNo"))
            {
                //throw new KeyNotFoundException("The config file doesn't contain the parameter \"TNo\". (the parameter names are case sensitive)");
            }
            if (!configParams.ContainsKey("Password"))
            {
                //throw new KeyNotFoundException("The config file doesn't contain the parameter \"Password\". (the parameter names are case sensitive)");
            }
            if (!configParams.ContainsKey("SearchQuery"))
            {
                throw new KeyNotFoundException("The config file doesn't contain the parameter \"SearchQuery\". (the parameter names are case sensitive)");
            }
            if (!configParams.ContainsKey("Name"))
            {
                throw new KeyNotFoundException("The config file doesn't contain the parameter \"Name\". (the parameter names are case sensitive)");
            }
            if (!configParams.ContainsKey("Gender"))
            {
                throw new KeyNotFoundException("The config file doesn't contain the parameter \"Gender\". (the parameter names are case sensitive)");
            }
            if (!configParams.ContainsKey("DateOfBirth"))
            {
                throw new KeyNotFoundException("The config file doesn't contain the parameter \"DateOfBirth\". (the parameter names are case sensitive)");
            }
            if (!configParams.ContainsKey("TimeOfBirth"))
            {
                throw new KeyNotFoundException("The config file doesn't contain the parameter \"TimeOfBirth\". (the parameter names are case sensitive)");
            }
            if (!configParams.ContainsKey("CountryOfBirth"))
            {
                throw new KeyNotFoundException("The config file doesn't contain the parameter \"CountryOfBirth\". (the parameter names are case sensitive)");
            }
            if (!configParams.ContainsKey("CityOfBirth"))
            {
                throw new KeyNotFoundException("The config file doesn't contain the parameter \"CountryOfBirth\". (the parameter names are case sensitive)");
            }

            // Get user birth details
            UserBirthPlaceDetails = GetPlaceDetails(configParams["CountryOfBirth"], configParams["CityOfBirth"]);
            if (!DateTime.TryParse(configParams["DateOfBirth"] + " " + configParams["TimeOfBirth"], out UserBirthDateTime))
            {
                Console.Error.WriteLine("Error parsing the User Date of Birth and Time of birth. Ignoring the data");
            }
            return configParams;
        }

        /// <summary>
        /// Logins into the telugu matrimony site and obtaines the cookies
        /// </summary>
        /// <param name="tNo"></param>
        /// <param name="password"></param>
        private static void GetTeluguMatrimonyLoginCookies(string tNo, string password)
        {
            string postContent = String.Format("ID={0}&PASSWORD={1}", tNo, password);
            MakePostRequest(LoginUrl, postContent);            
        }

        /// <summary>
        /// Gets User profile by scrapping telugu matrimony site for given TNo
        /// </summary>
        /// <param name="TNo"></param>
        /// <returns></returns>
        private static Stream GetUserProfile(string TNo)
        {
            string profileUrl = String.Format(ProfileUrlTemplate, TNo);            

            HttpWebRequest request = (HttpWebRequest)HttpWebRequest.Create(profileUrl);
            request.CookieContainer = TeluguMatrimonyCookies;
            try
            {
                HttpWebResponse response = (HttpWebResponse)request.GetResponse();
                if (response.StatusCode == HttpStatusCode.OK)
                {
                    return response.GetResponseStream();
                }
            }
            catch (WebException)
            {
            }
            return null;
        }

        /// <summary>
        /// Extracts the user information in the html doc.
        /// </summary>
        /// <param name="htmlDoc"></param>
        /// <returns></returns>
        private static Dictionary<string, Dictionary<string, string>> GetUserDetails(string TNo)
        {
            HtmlDocument htmlDoc = new HtmlDocument();
            Dictionary<string, Dictionary<string, string>> userInfo = new Dictionary<string, Dictionary<string, string>>();
                
            using (Stream stream = GetUserProfile(TNo))
            {
                htmlDoc.Load(stream);
            }

            try
            {

                // Getting Details
                HtmlNode detailsNode = htmlDoc.GetElementbyId("vp-details");
                HtmlNode parentInfoNodes = detailsNode.
                                            Descendants("div").
                                            Where(infoNode => infoNode.Attributes["class"] != null && infoNode.Attributes["class"].Value == "fleft").
                                            ElementAt(0).
                                            ParentNode;
                // converting the information into a dictionary
                string sectionHeader = String.Empty;
                string prefix = string.Empty;
                foreach (HtmlNode infoNode in parentInfoNodes.Descendants("div"))
                {
                    // check for main headers
                    if (infoNode.Attributes["class"] != null && infoNode.Attributes["class"].Value.Contains("boldtxt") && infoNode.Attributes["class"].Value.Contains("biggertxt"))
                    {
                        prefix = Sanitize(infoNode.InnerText);
                    }
                    // check for section headers div
                    if (infoNode.Attributes["class"] != null && infoNode.Attributes["class"].Value.Contains("boldtxt") && infoNode.Attributes["class"].Value.Contains("bigtxt"))
                    {
                        sectionHeader = Sanitize(infoNode.InnerText);
                        userInfo[prefix + "_" + sectionHeader] = new Dictionary<string, string>();
                    }
                    else if (infoNode.Attributes["class"] != null && infoNode.Attributes["class"].Value == "fleft")
                    {
                        IEnumerable<HtmlNode> subNodes = infoNode.Descendants("div").Where(node => node.Attributes["class"] != null && node.Attributes["class"].Value.Contains("fleft"));
                        if (subNodes.Count() >= 2)
                        {
                            int i = 0;
                            while (i < subNodes.Count())
                            {
                                userInfo[prefix + "_" + sectionHeader][Sanitize(subNodes.ElementAt(i).InnerText)] = Sanitize(subNodes.ElementAt(i + 1).InnerText);
                                i += 2;
                            }
                        }


                    }
                }
            }
            catch(Exception)
            {
            }
            return userInfo;
        }

        /// <summary>
        /// Get horoscope details from the Telugu matrimony based on TNo.
        /// </summary>
        /// <param name="TNo"></param>
        /// <returns></returns>
        private static Dictionary<string, string> GetHoroscopeDetails(string TNo)
        {
            Dictionary<string, string> horoscopeDetails = new Dictionary<string, string>();

            string horoscopeUrl = String.Format(HoroscopeUrlTemplate, TNo[1], TNo[2], TNo);
            
            HtmlDocument horoscopeDoc = new HtmlDocument();

            WebRequest request = WebRequest.Create(horoscopeUrl);
            try
            {
                HttpWebResponse response = (HttpWebResponse)request.GetResponse();
                if (response.StatusCode == HttpStatusCode.OK)
                {
                    horoscopeDoc.Load(response.GetResponseStream());
                    HtmlNode horoscopeNode = horoscopeDoc.DocumentNode.SelectNodes("//div[@class=\"smalltxt\"]").Where(node => node.InnerText.StartsWith("Name")).ElementAt(0);
                    string horoscope = Sanitize(horoscopeNode.InnerText);
                    horoscopeDetails = horoscope.Split('|').ToDictionary(keyValue => keyValue.Split(':')[0].Trim(), keyValue => String.Join(":",keyValue.Split(':').Skip(1)).Trim());
                }
            }
            catch (WebException)
            {
            }
            return horoscopeDetails;
        }

        /// <summary>
        /// Gets The horoscope scores based on the given name, birthdate, birthplace and ayanamsa
        /// </summary>
        /// <param name="candidateName"></param>
        /// <param name="candidateBirthDate"></param>
        /// <param name="candidateBirthPlace"></param>
        /// <param name="ayanamsa"></param>
        /// <returns></returns>
        private static Dictionary<string, Tuple<string,string>> GetMatchScores(string candidateName, DateTime candidateBirthDate, string candidateBirthPlace, string candidateBirthCountry, string ayanamsa)
        {
            Dictionary<string, Tuple<string,string>> matchScores = new Dictionary<string, Tuple<string,string>>();
            Dictionary<string, string> birthPlaceDetails = GetPlaceDetails("INDIA", candidateBirthPlace);
            if (birthPlaceDetails.Count > 0 && UserBirthPlaceDetails.Count > 0)
            {
                string candidateCountry = (birthPlaceDetails.ContainsKey("Country")) ? birthPlaceDetails["Country"] : String.Empty;
                string candidateCity = (birthPlaceDetails.ContainsKey("City")) ? birthPlaceDetails["City"] : String.Empty;
                string candidateLongitude = (birthPlaceDetails.ContainsKey("Longitude")) ? birthPlaceDetails["Longitude"] : String.Empty;
                string candidateLatitude = (birthPlaceDetails.ContainsKey("Latitude")) ? birthPlaceDetails["Latitude"] : String.Empty;
                string candidateTimeZone = (birthPlaceDetails.ContainsKey("Time Zone")) ? birthPlaceDetails["Time Zone"] : String.Empty;

                string candidateNSDirection = (!String.IsNullOrWhiteSpace(candidateLatitude)) ? candidateLatitude.Last().ToString() : String.Empty;
                string candidateEWDirection = (!String.IsNullOrWhiteSpace(candidateLongitude)) ? candidateLongitude.Last().ToString() : String.Empty;

                candidateLatitude = (candidateLatitude.Length > 2) ? candidateLatitude.Substring(0, candidateLatitude.Length - 2) : String.Empty;
                candidateLongitude = (candidateLongitude.Length > 2) ? candidateLongitude.Substring(0, candidateLongitude.Length - 2) : String.Empty;

                string userCountry = (UserBirthPlaceDetails.ContainsKey("Country")) ? UserBirthPlaceDetails["Country"] : String.Empty;
                string userCity = (UserBirthPlaceDetails.ContainsKey("City")) ? UserBirthPlaceDetails["City"] : String.Empty;
                string userLongitude = (UserBirthPlaceDetails.ContainsKey("Longitude")) ? UserBirthPlaceDetails["Longitude"] : String.Empty;
                string userLatitude = (UserBirthPlaceDetails.ContainsKey("Latitude")) ? UserBirthPlaceDetails["Latitude"] : String.Empty;
                string userTimeZone = (UserBirthPlaceDetails.ContainsKey("Time Zone")) ? UserBirthPlaceDetails["Time Zone"] : String.Empty;

                string userNSDirection = (!String.IsNullOrWhiteSpace(userLatitude)) ? userLatitude.Last().ToString() : String.Empty;
                string userEWDirection = (!String.IsNullOrWhiteSpace(userLongitude)) ? userLongitude.Last().ToString() : String.Empty;

                userLatitude = (userLatitude.Length > 2) ? userLatitude.Substring(0, userLatitude.Length - 2) : String.Empty;
                userLongitude = (userLongitude.Length > 2) ? userLongitude.Substring(0, userLongitude.Length - 2) : String.Empty;

                string boyDetails, girlDetails;

                if (ConfigParams["Gender"].ToLower()[0] == 'm')
                {
                    boyDetails = String.Format(MatchScoresBoyDetails, ConfigParams["Name"], UserBirthDateTime.Day, UserBirthDateTime.Month, UserBirthDateTime.Year, UserBirthDateTime.Hour, UserBirthDateTime.Minute, userCountry, userCity, userLongitude, userNSDirection, userLatitude, userEWDirection, userTimeZone);
                    girlDetails = String.Format(MatchScoresGirlDetails, candidateName, candidateBirthDate.Day, candidateBirthDate.Month, candidateBirthDate.Year, candidateBirthDate.Hour, candidateBirthDate.Minute, candidateCountry, candidateCity, candidateLongitude, candidateNSDirection, candidateLatitude, candidateEWDirection, candidateTimeZone);
                }
                else
                {
                    girlDetails = String.Format(MatchScoresGirlDetails, ConfigParams["Name"], UserBirthDateTime.Day, UserBirthDateTime.Month, UserBirthDateTime.Year, UserBirthDateTime.Hour, UserBirthDateTime.Minute, userCountry, userCity, userLongitude, userNSDirection, userLatitude, userEWDirection, userTimeZone);
                    boyDetails = String.Format(MatchScoresBoyDetails, candidateName, candidateBirthDate.Day, candidateBirthDate.Month, candidateBirthDate.Year, candidateBirthDate.Hour, candidateBirthDate.Minute, candidateCountry, candidateCity, candidateLongitude, candidateNSDirection, candidateLatitude, candidateEWDirection, candidateTimeZone);
                }

                string matchScoresPost = String.Format(MatchScoresPostRequestTemplate, boyDetails, girlDetails, (ayanamsa != "Chitra Paksha"));

                try
                {
                    using (Stream stream = MakePostRequest(MatchScoresUrl, matchScoresPost))
                    {
                        HtmlDocument doc = new HtmlDocument();
                        doc.Load(stream);
                        HtmlNode scoresNode = doc.GetElementbyId("AutoNumber1");
                        foreach (HtmlNode node in scoresNode.Descendants("tr").Skip(1).Where(node => node.Descendants("td").Count() == 5))
                        {
                            matchScores[Sanitize(node.Descendants("td").ElementAt(0).InnerText)] = new Tuple<string, string>(Sanitize(node.Descendants("td").ElementAt(2).InnerText), Sanitize(node.Descendants("td").ElementAt(4).InnerText));
                        }
                        HtmlNode totalScoreNode = doc.GetElementbyId("tscore1");
                        matchScores["Total"] = new Tuple<string,string>("Total", Sanitize(totalScoreNode.InnerText));
                    }
                }
                catch (Exception)
                {
                }

            }
            return matchScores;
        }

        /// <summary>
        /// Gets the place details like latitude, longitude, time offset etc for a given place
        /// </summary>
        /// <param name="cityName"></param>
        /// <returns></returns>
        private static Dictionary<string, string> GetPlaceDetails(string countryName, string cityName)
        {
            Dictionary<string, string> placeInformation = new Dictionary<string,string>();
            if(!String.IsNullOrWhiteSpace(cityName))
            {
                try
                {
                    using (Stream placeStream = MakePostRequest(PlaceFinderUrl, String.Format(PlaceFinderPostTemplate, countryName, cityName)))
                    {
                        HtmlDocument doc = new HtmlDocument();
                        doc.Load(placeStream);
                        HtmlNode placeDetailsNode = doc.GetElementbyId("AutoNumber2");
                        placeInformation = placeDetailsNode.Descendants("tr").Where(node => node.Descendants("td").Count() == 2).ToDictionary(node => Sanitize(node.Descendants("td").ElementAt(0).InnerText), node => Sanitize(node.Descendants("td").ElementAt(1).InnerText));
                    }
                }
                catch (Exception)
                {
                }
            }
            return placeInformation;
        }

        /// <summary>
        /// Performs the search in telugu matrimony and returns the list of T Nos.
        /// </summary>
        /// <returns></returns>
        private static IEnumerable<string> GetSearchTNos()
        {
            int startCount = 1;
            bool searchNext = true;
            List<string> TNos = new List<string>();            
            while (searchNext)
            {
                string searchPostRequestTemplate = ConfigParams["SearchQuery"] + SearchPostSuffixTemplate;
                try
                {
                    using (StreamReader streamReader = new StreamReader(MakePostRequest(SearchUrl, String.Format(searchPostRequestTemplate, startCount))))
                    {
                        string profiles = streamReader.ReadToEnd();
                        profiles = profiles.Split('~')[2];
                        Match match = searchTNoListRegex.Match(profiles);
                        if (match.Groups.Count > 1)
                        {
                            string profilesListString = match.Groups[1].Captures[0].Value;
                            string[] profilesList = profilesListString.Split(',');
                            startCount += profilesList.Length;
                            TNos.AddRange(profilesList);
                        }
                        else
                        {
                            searchNext = false;
                        }
                    }
                }
                catch (Exception)
                {
                }
            }
            return TNos;
        }

        private static string Sanitize(string word)
        {
            return Regex.Replace(WebUtility.HtmlDecode(word).Replace("\t", "").Replace("\n", "").Replace("\r", "").Trim(), "\\s+", " ");
        }

        private static Stream MakePostRequest(string url, string postContent)
        {
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
            byte[] postData = Encoding.UTF8.GetBytes(postContent);

            request.Method = "POST";
            request.Accept = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8";
            request.UserAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31";
            request.ContentType = "application/x-www-form-urlencoded";
            request.ContentLength = postData.Length;
            request.CookieContainer = TeluguMatrimonyCookies;
            using (Stream stream = request.GetRequestStream())
            {
                stream.Write(postData, 0, postData.Length);
            }

            HttpWebResponse response = (HttpWebResponse)request.GetResponse();

            return response.GetResponseStream();
        }

        private static void GetProfileData(string TNo, string[] inputColumns, out Dictionary<string, Dictionary<string, string>> candidateInfo, out Dictionary<string, string> candidateHoroscope, out Dictionary<string, Tuple<string, string>> matchScores)
        {
            candidateInfo = GetUserDetails(TNo);
            // adding missing keys
            if (!candidateInfo.ContainsKey("Personal Information_Basic Details"))
            {
                candidateInfo["Personal Information_Basic Details"] = new Dictionary<string, string>();
            }
            if (!candidateInfo.ContainsKey("Personal Information_Religious Information"))
            {
                candidateInfo["Personal Information_Religious Information"] = new Dictionary<string, string>();
            }
            if (!candidateInfo.ContainsKey("Personal Information_Location"))
            {
                candidateInfo["Personal Information_Location"] = new Dictionary<string, string>();
            }
            
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

        private static void PrintOutputLine(string TNo, Dictionary<string, Dictionary<string, string>> candidateInfo, Dictionary<string, string> candidateHoroscope, Dictionary<string, Tuple<string, string>> matchScores)
        {
            string outputLine = String.Join("\t", new string[] {
                                                                        TNo,
                                                                        (candidateInfo.ContainsKey("Personal Information_Basic Details") && candidateInfo["Personal Information_Basic Details"].ContainsKey("Name"))? candidateInfo["Personal Information_Basic Details"]["Name"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Basic Details") && candidateInfo["Personal Information_Basic Details"].ContainsKey("Age"))? candidateInfo["Personal Information_Basic Details"]["Age"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Basic Details") && candidateInfo["Personal Information_Basic Details"].ContainsKey("Height"))? candidateInfo["Personal Information_Basic Details"]["Height"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Basic Details") && candidateInfo["Personal Information_Basic Details"].ContainsKey("Eating Habits"))? candidateInfo["Personal Information_Basic Details"]["Eating Habits"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Religious Information") && candidateInfo["Personal Information_Religious Information"].ContainsKey("Caste / Sub Caste"))? candidateInfo["Personal Information_Religious Information"]["Caste / Sub Caste"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Religious Information") && candidateInfo["Personal Information_Religious Information"].ContainsKey("Gothram"))? candidateInfo["Personal Information_Religious Information"]["Gothram"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Religious Information") && candidateInfo["Personal Information_Religious Information"].ContainsKey("Star / Raasi"))? candidateInfo["Personal Information_Religious Information"]["Star / Raasi"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Religious Information") && candidateInfo["Personal Information_Religious Information"].ContainsKey("Kuja Dosham"))? candidateInfo["Personal Information_Religious Information"]["Kuja Dosham"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Location") && candidateInfo["Personal Information_Location"].ContainsKey("City"))? candidateInfo["Personal Information_Location"]["City"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Location") && candidateInfo["Personal Information_Location"].ContainsKey("State"))? candidateInfo["Personal Information_Location"]["State"] : String.Empty,
                                                                        (candidateInfo.ContainsKey("Personal Information_Location") && candidateInfo["Personal Information_Location"].ContainsKey("Country"))? candidateInfo["Personal Information_Location"]["Country"] : String.Empty,
                                                                        (candidateHoroscope.ContainsKey("Date of Birth"))? candidateHoroscope["Date of Birth"] : String.Empty,
                                                                        (candidateHoroscope.ContainsKey("Time of Birth (Hr.Min.Sec)"))? candidateHoroscope["Time of Birth (Hr.Min.Sec)"] : String.Empty,
                                                                        (candidateHoroscope.ContainsKey("Time Zone (Hr.Min.Sec)"))? candidateHoroscope["Time Zone (Hr.Min.Sec)"] : String.Empty,
                                                                        (candidateHoroscope.ContainsKey("Place of Birth"))? candidateHoroscope["Place of Birth"] : String.Empty,
                                                                        (matchScores.ContainsKey("Varna (For work)"))? matchScores["Varna (For work)"].Item2 : String.Empty,
                                                                        (matchScores.ContainsKey("Vashya (Personal relations)"))? matchScores["Vashya (Personal relations)"].Item2 : String.Empty,
                                                                        (matchScores.ContainsKey("Tara (For destiny)"))? matchScores["Tara (For destiny)"].Item2 : String.Empty,
                                                                        (matchScores.ContainsKey("Yoni (For mental compatibility)"))? matchScores["Yoni (For mental compatibility)"].Item2 : String.Empty,
                                                                        (matchScores.ContainsKey("Graha (For nature)"))? matchScores["Graha (For nature)"].Item2 : String.Empty,
                                                                        (matchScores.ContainsKey("Gan (For social relations)"))? matchScores["Gan (For social relations)"].Item2 : String.Empty,
                                                                        (matchScores.ContainsKey("Bhakut (For life)"))? matchScores["Bhakut (For life)"].Item2 : String.Empty,
                                                                        (matchScores.ContainsKey("Nadi (For physical compatibly)"))? matchScores["Nadi (For physical compatibly)"].Item2 : String.Empty,                                                                            
                                                                        (matchScores.ContainsKey("Total"))? matchScores["Total"].Item2 : String.Empty,
                                                                    });
            Console.WriteLine(outputLine);
        }
        private static void PrintOutputLine(string line)
        {
            Console.WriteLine(line);
        }
    }    
}
