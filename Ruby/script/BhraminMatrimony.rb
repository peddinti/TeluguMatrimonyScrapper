require 'rubygems'
require 'mechanize'
require 'parallel'

# Constants
LoginPageUrl = 'http://www.brahminmatrimony.com/login/'
LoginSubmitUrl = 'https://communitymatrimony.com/login/logincheck.php'
HomeUrl = 'http://www.brahminmatrimony.com'

SavedSearchId = "1490167"
# SavedSearchId = "1515915"
SearchType = "2"
SavedSearchUrl = "http://www.brahminmatrimony.com/search/index.php?act=srchresult&srchId=%s&srchType=%s"

ProfileUrl = "http://www.brahminmatrimony.com/viewprofile/index.php?act=fullprofilenew&id=?"
ProfilePostParams = {"Opposite_MatriId":"BRH1861562","MatriId":"BRH979990","Gender":"1","PaidStatus":"0","CommunityId":"25","Source":"2","MaritalStatus":"1","RequestFor":1,"SoftIcon":1,"LocationIcon":1,"CommonInterest":1,"EncryptId":"e2b3279080dea1a0e0a1de79645f9a2a0ef2a9d1","ApiFile":"ProDet","PPWeb":1,"OutputType":2,"AppType":10,"TrustBadge":1,"Module":"Profiledetail","Referrer":"List_View","UniqueId":"5847acb386f9d","Field_Empty":1,"Field_Label":1}
ProfileMasterParams = {}
ProfileDetailsUrl = "http://www.brahminmatrimony.com/api/viewprofile.php/"
PhotoRequestUrl = 'http://www.brahminmatrimony.com/request/request.php?rno=0.7894592644334861'

ProfileKeys = ["tNo", "photo_url", "Name", "Age", "Height", "Weight", "Body Type", "Complexion", "Mother Tongue", "Physical Status", "Star", "Raasi", "Gothra", "Chevvai Dosham", "Caste/Division", "Subcaste", "State", "City", "Gender", "About Myself", "Profile Created For", "Languages Known", "Country", "Citizenship", "Education Detail", "Employed in", "Occupation", "Occupation Detail", "Annual Income", "Education", "Professional Info", "Family Value", "Family Type", "Family Status", "Father's Occupation", "Mother's Occupation", "Father Name", "Mother Name", "Father Native Place", "Mother Native Place", "Father House Name", "Mother House Name", "Family Origin", "Brothers Married", "No.of Brothers", "Sisters Married", "No.of sisters", "No.of Siblings", "About Family", "Member Family Info", "HOROSCOPEURL", "BIRTH_CITY_NAME", "BIRTHTIME", "BIRTHDATESTR", "Marital Status", "Hobbies", "Interests", "Music", "last_login"]
# Globals

def printHeaders(file)
  file.puts ProfileKeys.join("\t")
end

def printProfile(file,profile)
  values = ProfileKeys.map{|key| profile[key]}.map{|v| v.blank?? v : v.gsub("\n", '').gsub("\r", '').gsub("\t", ' ')}
  file.puts values.join("\t").encode("UTF-8", invalid: :replace, undef: :replace).gsub("\r", '')
end

def getProfile(client, tNo)
  profile = {}
  params = ProfilePostParams.clone
  params[:Opposite_MatriId] = tNo

  details = client.post(ProfileDetailsUrl, params).body
  details = details.gsub("\r", "").gsub("\n", "")
  details = eval(details)
  member_info = details[:MEMBERINFO]
  profile["last_login"] = member_info[:STATUS][:LAST_LOGIN]
  profile["tNo"] = tNo
  profile.merge! Hash[member_info[:BASICINFORMATION].values.map{|v| [v[:"1"], v[:"2"]]}]
  profile.merge! Hash[member_info[:BASICDETAILS].values.map{|v| [v[:"1"], v[:"2"]]}]
  profile.merge! Hash[member_info[:RELIGIOUSINFO].values.map{|v| [v[:"1"], v[:"2"]]}]
  profile.merge! Hash[member_info[:RESIDENCE].values.map{|v| [v[:"1"], v[:"2"]]}]
  profile.merge! Hash[member_info[:PROFESSIONALINFO].values.map{|v| [v[:"1"], v[:"2"]]}]
  profile.merge! Hash[member_info[:PROFESSIONALDETAIL].values.map{|v| [v[:"1"], v[:"2"]]}]

  member_family_info = details[:MEMBERFAMILYINFO]
  profile.merge! Hash[member_family_info.values.map{|v| [v[:"1"], v[:"2"]]}]

  profile.merge! Hash[details[:MEMBERLIFESTYLEINFO].values.map{|v| [v[:"1"], v[:"2"]]}]

  photo_info = details[:MEMBERPHOTOINFO]
  unless photo_info[:NORMAL].blank?
    ids = photo_info[:NORMAL].split(", ")
    profile["photo_url"] = photo_info[:PHOTOPATH] + "/" + ids.first
  end
  horoscope_info = details[:HOROSCOPEINFO]
  unless horoscope_info.blank?
    profile["HOROSCOPEURL"] = horoscope_info[:HOROSCOPEURL]
    profile["BIRTH_CITY_NAME"] = horoscope_info[:CITY_NAME]
    profile["BIRTHTIME"] = horoscope_info[:BIRTHTIME]
    profile["BIRTHDATESTR"] = horoscope_info[:BIRTHDATESTR]
  end

  #profile.merge! Hash[details[:LASTCONVERSATION].values.map{|v| [v[:"1"], v[:"2"]]}]
  #member_partner_info = details[:MEMBERPARTNERINFO]
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

def login(client)
  client.request_headers['Referer'] = LoginPageUrl
  client.request_headers['Origin'] = HomeUrl
  client.get(LoginPageUrl)

  t = client.post(LoginSubmitUrl, {"frmLoginSubmit" => "yes",
                              "communityId" => "25",
                              "idEmail" => "BRH979990",
                              "password" => "1234a5",
                              "STAYLOGIN" => "yes",
                              "frmsubmit" => "Login",
                              "PRIV_NAME" => "",
                              "PRIV_COUNTRY" => "91",
                              "PRIV_PHONE" => "9670289267"
  })
  if t.code == '302'
    client.request_headers["Host"] = "www.brahminmatrimony.com"
    client.get(t.header["location"])
  end
end

def sendPhotoRequest(client, tNo)
  client.request_headers['Referer'] = "http://www.brahminmatrimony.com/viewprofile/index.php?act=fullprofilenew&par=yes&id=#{tNo}"
  client.request_headers['X-Requested-With'] = 'XMLHttpRequest'
  client.request_headers['Host'] = 'www.brahminmatrimony.com'
  formData = {
      "OppMatriId" => tNo,
      "ReqId" => "1",
      "ReutrnFormat" => "json",
      "Referrer" => "",
      "TrackPage" => "viewprofile"
  }
  response = client.post(PhotoRequestUrl, formData)
  unless response.body.blank?
    return JSON.parse(response.body)
  end
  return nil
end

client = Mechanize.new { |agent|
  agent.user_agent_alias = 'Mac Safari'
  agent.redirect_ok = false
}

client.request_headers = {
    "Accept-Encoding" => "gzip, deflate, br",
    "Accept-Language" => "en-US,en;q=0.8",
    "Upgrade-Insecure-Requests" => 1,
    "Accept" => "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Connection" => "keep-alive",
    "Content-Type" => "application/x-www-form-urlencoded",
    "Host" => "communitymatrimony.com",
    "Origin" => "http://www.brahminmatrimony.com",
    "Referer" => "http://www.brahminmatrimony.com/login/logout.php"
}
TNos = []
login(client)
search_url = SavedSearchUrl % [SavedSearchId, SearchType]
search_page = client.get(search_url)
search_form = search_page.form_with(:name => "frmSearchConds")
client.request_headers["Referer"] = SavedSearchUrl % [SavedSearchId, SearchType]
client.request_headers["X-Requested-With"] = "XMLHttpRequest"
search_form.action = "http://www.brahminmatrimony.com/search/search_ctrl.php?first=1&rno=0.2131385597137483"
search_results = search_form.submit
values = search_results.body.split("#");
total_count = values[2]

# adding view
search_form["view"] = total_count
search_form["Page"] = 1
search_results = search_form.submit;
values = search_results.body.split("#");
results = eval(values[10]);
TNos = results.map{|r| r[:ID]}
pp = client.get(ProfileUrl % TNos[0])
values = pp.at("script:contains('sessMatriId')").inner_text.gsub("\n", '').gsub("\r",'').gsub("\t",'').split(";")
values = values.select{|v| (v.starts_with? "msgs") && (!v.include? "JSON")}.map{|v| v.split("= ")}
values = values.map{|v| [v[0].gsub("msgs[", '').gsub("]", '').strip(), v[1].strip()]}
ProfileMasterParams = Hash[values.map{|v| [eval(v[0]), eval(v[1])]}]
unless ProfileMasterParams['EncryptId'].blank?
  ProfilePostParams[:EncryptId] = ProfileMasterParams['EncryptId']
end
unless ProfileMasterParams['UniqueId'].blank?
  ProfilePostParams[:UniqueId] = ProfileMasterParams['UniqueId']
end

profiles = Parallel.map(TNos, in_threads: 5) {|tNo| getProfileWrapper(client, tNo)}
puts "Finished getting profiles"
# Dumping all the profile data as json
file = File.open("./bhramin_profiles.txt", 'w')
file.write(profiles)
file.close()

# writing the data
file = File.open("./bhramin_matches.tsv", 'w')
printHeaders(file)
profiles.each do |profile|
  printProfile(file, profile)
end
file.close()






