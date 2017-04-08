require 'rubygems'
require 'mechanize'
require 'parallel'

# Constants
HomeUrl = 'http://parinayavedika.com/Default.aspx'
AdminUrl = 'http://www.parinayavedika.com/ajaxpro/PVAdmin.PVAdmin,PVAdmin.ashx'
SavedSearchId = "423"
SavedSearchUrl = "http://www.parinayavedika.com/SearchResults.aspx?SSID="
SearchResultsUrl = 'http://www.parinayavedika.com/ajaxpro/PVAdmin.SearchResults,PVAdmin.ashx'
ProfileUrl = 'http://www.parinayavedika.com/ajaxpro/PVAdmin.ViewProfile,PVAdmin.ashx'
EditProfileUrl = 'http://www.parinayavedika.com/ajaxpro/PVAdmin.EditProfile,PVAdmin.ashx'

# Dynamic Constants
SavedSearchName = 'VMK-Broad'

# Globals
MSMapping = {}
ComplexionMapping = {}
StarMapping = {}
GothramMapping = {}
EducationMapping = {}
CasteMapping = {}
SectMapping = {}
EconomicStatusMapping = {}
MotherToungeMapping = {}
SubSectMapping = {}
FamilyTypeMapping = {}

def parseTableContent(content)
  content = JSON.parse(content.chomp(";/*"))
  content = JSON.parse(content[1]).values.flatten
  return content
end

def getDict(client, action)
  content = client.post(AdminUrl,
         '{"nCode":0}',
         {"X-AjaxPro-Method" => action}).body
  content = eval(eval(content.gsub(";/*", ''))).values.first
  Hash[content.map{|t| t.values.take(2)}]
end

def printHeaders(file)
  file.puts "ID\tProfileUrl\tImage Url\tFirstName\tLastName\tEmail\tPhoneNo\tLandLine\tDOB\tTOB\tAge\tHeight\t"\
       "Marital Status\tComplexion\tCity\tFamily Type\tMother Tonge\tEconomic Status\tAbout\t"\
       "Star\tPadam\tGothram\tCaste\tSect\tSubSect\t"\
       "Education\tInstitution\tPosition\tEmployment\tAnnual Income\tRelocate"
end

def printProfile(file,profile)
  keys = [:UM_Var_UserID, :profile_url, :image_url, :UM_Var_FirstName, :UM_Var_LastName, :UM_Var_EmailID,
          :UM_Var_MobileNo, :UM_Var_LandlineNo, :UM_DT_DOB, :UM_Var_TOB, :UM_Int_Age, :UM_Var_Height, :UM_Int_MStatus,
          :UM_Int_Complexion, :UM_Var_POB_City, :UM_Int_FamilyType, :UM_Int_MotherTongue, :UM_Int_EconomicStatus,
          :UM_Var_AboutMyFamily, :UM_Int_BirthStar, :UM_Int_Paadam, :UM_Int_Gothram, :UM_Int_Caste, :UM_Int_Sect,
          :UM_Int_SubSect, :UM_Int_EducationLevel, :UEE_Var_EDU_Institution, :UEE_Var_CurrentDesignation,
          :UEE_Var_Emp_Details, :UEE_Int_Emp_AnnualIncome, :UEE_smallint_Emp_Relocate]
  values = keys.map{|key| profile[key]}
  file.puts values.join("\t").encode("UTF-8", invalid: :replace, undef: :replace).gsub("\r", '')

end

def getProfile(client, tNo)
  profile = {}
  client.request_headers["Referer"] = "http://www.parinayavedika.com/ViewProfile.aspx?SRID=#{tNo}"
  profile_page = client.post(ProfileUrl,
                             "{\"strRUserID\":\"#{tNo}\",\"nLoggedIn\":\"1\"}",
                             {"X-AjaxPro-Method" => "GetRequestUserInfo"})
  unless profile_page.body.blank?
    profile = parseTableContent(profile_page.body).reduce({}, :merge)
    profile = profile.inject({}){|memo,(k,v)| memo[k.to_sym] = v; memo}
  end

  # converting ids to values
  profile[:UM_Int_MStatus] = MSMapping[profile[:UM_Int_MStatus]]
  profile[:UM_Int_Complexion] = ComplexionMapping[profile[:UM_Int_Complexion]]
  profile[:UM_Int_BirthStar] = StarMapping[profile[:UM_Int_BirthStar]]
  profile[:UM_Int_Gothram] = GothramMapping[profile[:UM_Int_Gothram]]
  profile[:UM_Int_EducationLevel] = EducationMapping[profile[:UM_Int_EducationLevel]]
  profile[:UM_Int_Caste] = CasteMapping[profile[:UM_Int_Caste]]
  profile[:UM_Int_Sect] = SectMapping[profile[:UM_Int_Sect]]
  profile[:UM_Int_EconomicStatus] = EconomicStatusMapping[profile[:UM_Int_EconomicStatus]]
  profile[:UM_Int_MotherTongue] = MotherToungeMapping[profile[:UM_Int_MotherTongue]]
  profile[:UM_Int_SubSect] = SubSectMapping[profile[:UM_Int_SubSect]]
  profile[:UM_Int_FamilyType] = FamilyTypeMapping[profile[:UM_Int_FamilyType]]
  matches = /\/Date\(([\d\+]+)\)\//.match(profile[:UM_DT_DOB])
  if (matches.size > 1)
    profile[:UM_DT_DOB] = Time.at(eval(matches[1]) / 1000)
  end
  matches = /\/Date\(([\d\+]+)\)\//.match(profile[:UM_Dt_RegistrationDate])
  if (matches.size > 1)
    profile[:UM_Dt_RegistrationDate] = Time.at(eval(matches[1]) / 1000)
  end

  # getting photos
  images_page = client.post(EditProfileUrl,
                            "{\"strUserID\":\"#{tNo}\"}",
                            {"X-AjaxPro-Method" => "GetUserPhotos"})
  unless images_page.body.blank?
    profile[:image_url] = eval(images_page.body.chomp(";/*"))[1].split("$").first
    profile[:image_url] = "http://www.parinayavedika.com/#{profile[:image_url]}"
  end

  profile[:profile_url] = "http://www.parinayavedika.com/ViewProfile.aspx?SRID=#{tNo}"
  profile[:UM_Var_AboutMyFamily] = profile[:UM_Var_AboutMyFamily] || ""
  profile[:UM_Var_AboutMyFamily] = profile[:UM_Var_AboutMyFamily].gsub("\n", "").gsub!("\r","")

  profile
end

def getProfileWrapper(client, tNo)
  limit = 3
  begin
    begin
      profile = getProfile(client, tNo)
      return profile
    rescue Exception => ex
      puts "Exception: #{tNo}; #{ex}"
      limit-=1
    end
  end while (limit > 0)
end

def js_to_hash(lines)
  Hash[lines.map{|line|
    line.gsub(';', '').gsub('var ', '').split(' = ')
  }]
end

a = Mechanize.new { |agent|
  agent.user_agent_alias = 'Mac Safari'
  agent.redirect_ok = false
}

a.request_headers = {
    "Accept-Encoding" => "gzip, deflate, sdch",
    "Accept-Language" => "en-US,en;q=0.8",
    "Upgrade-Insecure-Requests" => 1,
    "Accept" => "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection" => "keep-alive"
}
TNos = []
a.get(HomeUrl)
login_headers = a.request_headers
a.post(AdminUrl, '{"strUserName": "pv11479", "strPassword": "peddinti@1"}', {"X-AjaxPro-Method" => "LoginUser"})
a.request_headers['Referer'] = 'http://www.parinayavedika.com/search.aspx'
search_base_page = a.get(SavedSearchUrl+SavedSearchId)
search_params = search_base_page.at("script:contains('m_strSearchQuery')")
unless search_params.blank?
  search_params = search_params.inner_text.split("\r\n").select{|v| !v.blank?}.map{|v| v.strip}
  # converting in to hash object
  search_params = js_to_hash(search_params)
end
a.request_headers['Referer'] = SavedSearchUrl+SavedSearchId
search_results_page = a.post(SearchResultsUrl,
                        "{\"strSesUserId\":\"#{eval(search_params['m_strUserId'])}\",\"nLoggedIn\":#{eval(search_params['m_strLoggedIn'])},\"strSearchQuery\":\"#{eval(search_params['m_strSearchQuery'])}\"}",
                        {"X-AjaxPro-Method" => "GenerateSearchResults"})

search_results = nil
unless search_results_page.body.blank?
  search_results = parseTableContent(search_results_page.body)
end
TNos = search_results.map{|result| result[:UM_Var_UserID]}
# creating a dictionary for all casts and sub casts
GothramMapping = getDict(a, "GetGothramsMaster")
CasteMapping = getDict(a, "GetCastesMaster")
EducationMapping = getDict(a, "GetEducationLevel")
MSMapping = getDict(a, "GetMaritalStatus")
ComplexionMapping = getDict(a, "GetSkinComplexion")
StarMapping = getDict(a, "GetStarsMaster")
MotherToungeMapping = getDict(a, "GetMotherTongue")
FamilyTypeMapping = getDict(a, "GetFamilyType")
EconomicStatusMapping = getDict(a, "GetEconomicStatus")
SectMapping = getDict(a, "GetCastesSectMaster")
SubSectMapping = getDict(a, "GetCasteSubsectMaster")


profiles = Parallel.map(TNos, in_threads: 5) {|tNo| getProfileWrapper(a, tNo)}
puts "Finished getting profiles"
# Dumping all the profile data as json
file = File.open("./parinaya_profiles.txt", 'w')
file.write(profiles)
file.close()

# writing the data
file = File.open("./parinaya_matches.tsv", 'w')
printHeaders(file)
profiles.each do |profile|
  printProfile(file, profile)
end
file.close()






