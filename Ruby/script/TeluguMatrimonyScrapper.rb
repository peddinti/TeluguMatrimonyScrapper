require 'rubygems'
require 'mechanize'
require 'parallel'

# Constants
HomeUrl = 'http://profile.telugumatrimony.com/login/myhome.php?MS=1'
ProfileUrlTemplate = "http://profile.telugumatrimony.com/profiledetail/viewprofile.php?id=%s"
HoroscopeUrlTemplate = "http://profile.telugumatrimony.com/horoscope/bulkhoroscopes.php?loginid=%s&partnerid=%s"
LoginUrl = 'http://profile.telugumatrimony.com/login/login.php'
SearchUrl = 'http://profile.telugumatrimony.com/search/fetchrsearchresult_ql.php'
SavedSearchUrl = "http://profile.telugumatrimony.com/search/savedsearchpost.php?searchid=%s&gaact=SLTSAVSRCH&gasrc=NAVSRCH"
PhoneUrl = 'http://profile.telugumatrimony.com/assuredcontact/assuredinsertphonerequest.php'

# Dynamic Constants
#SavedSearchName = 'Search VMK'
#SavedSearchName = 'Broad VMK'
SavedSearchName = 'VMK-All'
SavedSearchId = 4

def printHeaders(file)
  file.puts "TNo\tProfileUrl\tAbout\tName\tAge\tHeight\tWeight\tMother Tongue\tMarital Status\tBody Type\tComplexion\t"\
       "Physical Status\tEating Habits\tDrinking Habits\tSmoking Habits\t"\
       "Religion\tCaste\tGothram\tStar\tDosham\t" \
       "Country\tState\tCitizenship\tCity\t"\
       "Education\tEducation Detail\tOccupation\tOccupation Detail\tEmployed\tIncome\t" \
       "Values\tType\tStatus\tFather Status\tMother Status\tOrigin\tBrothers\tSisters\tLocation\tAbout\tHoroscope Pct\t"\
       "Action Title\tAction Date\tAction Description"
end

def printProfile(file,profile)
  values = []
  profile[:image_urls] = profile[:image_urls].blank? ? [] : profile[:image_urls]
  values.concat([profile[:tno], profile[:image_urls].join('|')])
  bi = profile[:basic_info]
  bi[:about] = bi[:about].blank? ? "" : bi[:about]
  values.concat([bi[:about].gsub("\n", " "), bi[:name], bi[:age], bi[:height], bi[:weight], bi[:mother_tongue], bi[:marital_status],
                 bi[:body_type], bi[:complexion], bi[:physical_status], bi[:eating_habits], bi[:drinking_habits], bi[:smoking_habits]])
  ri = profile[:religion_info]
  values.concat([ri[:religion], ri[:caste], ri[:gothram], ri[:star], ri[:dosham]])
  li = profile[:location_info]
  values.concat([li[:country], li[:state], li[:citizenship], li[:city]])
  pi = profile[:professional_info]
  values.concat([pi[:education], pi[:education_detail], pi[:occupation], pi[:occupation_detail], pi[:employed], pi[:income]])
  fi = profile[:family_info]
  fi[:about] = fi[:about].blank? ? "" : fi[:about]
  values.concat([fi[:values], fi[:type], fi[:status], fi[:father_status], fi[:mother_status], fi[:origin],
                 fi[:brothers], fi[:sisters], fi[:location], fi[:about].gsub("\n", " ").gsub("\t", "")])
  values.concat([profile[:horoscope][:match_pct]])
  ai = profile[:action_info]
  values.concat([ai[:title], ai[:last_date], ai[:description]])
  file.puts values.join("\t").encode("UTF-8", invalid: :replace, undef: :replace).gsub("\r", '').gsub("\n",'')
end

def getProfile(client, tNo)
  profile = {}
  profile_page = client.get(ProfileUrlTemplate % tNo)
  about_info = profile_page.at('.newvp-aboutinfo-icon')
  unless about_info.blank?
    about_info = about_info.parent
  end
  basic_info = profile_page.at('.newvp-basicinfo-icon')
  unless basic_info.blank?
    basic_info = basic_info.parent
  end
  religion_info = profile_page.at('.newvp-relgninfo-icon')
  unless religion_info.blank?
    religion_info = religion_info.parent
  end
  location_info = profile_page.at('.newvp-locinfo-icon')
  unless location_info.blank?
    location_info = location_info.parent
  end
  professional_info = profile_page.at('.newvp-profinfo-icon')
  unless professional_info.blank?
    professional_info = professional_info.parent
  end
  family_info = profile_page.at('.newvp-famlyinfo-icon')
  unless family_info.blank?
    family_info = family_info.parent
  end
  image_matches = /PhotoPagination\(([^\)]+)\)/.match(profile_page.at("script:contains('PhotoPagination')").inner_text)
  image_urls = eval(image_matches[1].split(',')[2])
  unless image_urls.blank?
    profile[:image_urls] = image_urls.split('^')
  end

  profile[:tno] = tNo
  profile[:basic_info] = {}
  unless about_info.blank?
    profile[:basic_info][:about] = about_info.at("#profilesubstrdesc").inner_text.strip()
  end
  unless basic_info.blank?
    profile[:basic_info][:name] = basic_info.at("div[text() = 'Name'] ~ div").inner_text.strip
    profile[:basic_info][:age] = basic_info.at("div[text() = 'Age'] ~ div").inner_text.strip
    profile[:basic_info][:height] = basic_info.at("div[text() = 'Height'] ~ div").inner_text.strip
    profile[:basic_info][:weight] = basic_info.at("div[text() = 'Weight'] ~ div").inner_text.strip
    profile[:basic_info][:mother_tongue] = basic_info.at("div[text() = 'Mother Tongue'] ~ div").inner_text.strip
    profile[:basic_info][:marital_status] = basic_info.at("div[text() = 'Marital Status'] ~ div").inner_text.strip
    profile[:basic_info][:body_type] = basic_info.at("div[text() = 'Body Type'] ~ div").inner_text.strip
    profile[:basic_info][:complexion] = basic_info.at("div[text() = 'Complexion'] ~ div").inner_text.strip
    profile[:basic_info][:physical_status] = basic_info.at("div[text() = 'Physical Status'] ~ div").inner_text.strip
    profile[:basic_info][:eating_habits] = basic_info.at("div[text() = 'Eating Habits'] ~ div").inner_text.strip
    profile[:basic_info][:drinking_habits] = basic_info.at("div[text() = 'Drinking Habits'] ~ div").inner_text.strip
    profile[:basic_info][:smoking_habits] = basic_info.at("div[text() = 'Smoking Habits'] ~ div").inner_text.strip
  end

  profile[:religion_info] = {}
  unless religion_info.blank?
    religion = religion_info.at("div[text() = 'Religion'] ~ div")
    profile[:religion_info][:religion] = religion.blank? ? nil : religion.inner_text.strip
    caste = religion_info.at("div[text() = 'Caste / Sub Caste'] ~ div")
    profile[:religion_info][:caste] = caste.blank? ? nil : caste.inner_text.strip
    gothram = religion_info.at("div[text() = 'Gothram '] ~ div")
    profile[:religion_info][:gothram] = gothram.blank? ? nil : gothram.inner_text.strip
    star = religion_info.at("div[text() = 'Star / Raasi'] ~ div")
    profile[:religion_info][:star] = star.blank? ? nil : star.inner_text.strip
    dosham = religion_info.at("div[text() = 'Dosham'] ~ div")
    profile[:religion_info][:dosham] = dosham.blank? ? nil : dosham.inner_text.strip
  end

  profile[:location_info] = {}
  unless location_info.blank?
    country = location_info.at("div[text() = 'Country'] ~ div")
    profile[:location_info][:country] = country.blank? ? nil :  country.inner_text.strip
    state = location_info.at("div[text() = 'State'] ~ div")
    profile[:location_info][:state] = state.blank? ? nil : state.inner_text.strip
    citizenship = location_info.at("div[text() = 'Citizenship'] ~ div")
    profile[:location_info][:citizenship] = citizenship.blank? ? nil :  citizenship.inner_text.strip
    city = location_info.at("div[text() = 'City'] ~ div")
    profile[:location_info][:city] = city.blank? ? nil : city.inner_text.strip
  end

  profile[:professional_info] = {}
  unless professional_info.blank?
    profile[:professional_info][:education] = professional_info.at("div[text() = 'Education'] ~ div").inner_text.strip
    profile[:professional_info][:education_detail] = professional_info.at("div[text() = 'Education in Detail'] ~ div").inner_text.strip
    profile[:professional_info][:occupation] = professional_info.at("div[text() = 'Occupation'] ~ div").inner_text.strip
    od = professional_info.at("div[text() = 'Occupation in Detail'] ~ div")
    profile[:professional_info][:occupation_detail] = od.blank? ? nil : od.inner_text.strip
    emp = professional_info.at("div[text() = 'Employed in'] ~ div")
    profile[:professional_info][:employed] = emp.blank? ? nil : emp.inner_text.strip
    inc = professional_info.at("div[text() = 'Annual Income'] ~ div")
    profile[:professional_info][:income] = inc.blank? ? nil : inc.inner_text.strip
  end

  profile[:family_info] = {}
  unless family_info.blank?
    val = family_info.at("div[text() = 'Family Values'] ~ div")
    profile[:family_info][:values] = val.blank? ? nil : val.inner_text.strip
    type = family_info.at("div[text() = 'Family Type'] ~ div")
    profile[:family_info][:type] = type.blank? ? nil : type.inner_text.strip
    status = family_info.at("div[text() = 'Family Status'] ~ div")
    profile[:family_info][:status] = status.blank? ? nil : status.inner_text.strip
    father_status = family_info.at("div[text() = \"Father's Status\"] ~ div")
    profile[:family_info][:father_status] = father_status.blank? ? nil : father_status.inner_text.strip
    origin = family_info.at("div[text() = 'Ancestral Origin'] ~ div")
    profile[:family_info][:origin] = origin.blank? ? nil : origin.inner_text.strip
    brothers = family_info.at("div[text() = 'No of Brother(s)'] ~ div")
    profile[:family_info][:brothers] = brothers.blank? ? nil : brothers.inner_text.strip
    sisters = family_info.at("div[text() = 'No of Sister(s)'] ~ div")
    profile[:family_info][:sisters] = sisters.blank? ? nil : sisters.inner_text.strip
    mother_status = family_info.at("div[text() = \"Mother's Status\"] ~ div")
    profile[:family_info][:mother_status] = mother_status.blank? ? nil : mother_status.inner_text.strip
    loc = family_info.at("div[text() = 'Family Location'] ~ div")
    profile[:family_info][:location] = loc.blank? ? nil : loc.inner_text.strip
    about = family_info.at("div[text() = 'About our family'] ~ div")
    profile[:family_info][:about] = about.blank? ? nil : about.inner_text.strip
  end

  profile[:horoscope] = {}
  horoscope = client.get(HoroscopeUrlTemplate % ['T2247456', tNo])
  profile[:horoscope][:match_pct] = horoscope.body.split('~')[1]

  # action Box
  action_info = profile_page.at("div#ShowActionBtn").at("div#titleDisp").parent
  profile[:action_info] = {}
  unless action_info.blank?
    profile[:action_info][:title] = action_info.search("span")[0].inner_text
    profile[:action_info][:last_date] = action_info.search("span")[1].inner_text
    profile[:action_info][:description] = action_info.at("#titleDisp").inner_text
  end
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
  page = client.get(LoginUrl)
  form = page.forms.select{|f| f.name == 'Login'}[1]
  form.MIDP = "T2247456"
  form.PASSWORD2 = "1234a"
  form.submit
  client.request_headers['cookie'] = client.cookies.map {|c| "#{c.name}=#{c.value};"}.join(" ")
end

def scrapeSavedSearch(client, filePathPrefix)
  loggedin_page = client.get(HomeUrl)
  saved_search = loggedin_page.search(".fixed-topnav-dropdown-content").at("div[text()='#{SavedSearchName}'] ~ div>a")
  if (saved_search.blank?)
    # going via Id model
    search_form = client.get(SavedSearchUrl % [SavedSearchId]).forms.first
  else
    search_form = client.click(saved_search).forms.first
  end
  search_results = search_form.submit
  stlimit = 11
  search_more_form = search_results.form_with(:name => "srchmore")
  search_more_form.randid = "a1710s"
  search_more_form.facet = "N"
  search_more_form.add_field!('STLIMIT', stlimit)
  begin
    t1,count, data, t2 = search_results.search("script:contains('var Jsg_json_data')").first.inner_text.split('~')
    data = JSON.parse(data)["profiles"]
    TNos.concat data.map{|t| t["PHOTOLIKEDID"]}
    search_more_form.STLIMIT = stlimit
    search_more_form.action = SearchUrl
    search_results = search_more_form.submit
    stlimit += data.size
    puts "Searching with start: #{stlimit}. Got result count: #{data.size}"
  end while data.size > 0

  puts "Getting #{TNos.size} Profiles"
  profiles = Parallel.map(TNos, in_threads: 5) {|tNo| getProfileWrapper(client, tNo)}
  puts "Finished getting profiles"
  # Dumping all the profile data as json
  file = File.open(filePathPrefix + "_profiles.txt", 'w')
  file.write(profiles)
  file.close()

  # writing the data
  file = File.open(filePathPrefix + "_matches.tsv", 'w')
  printHeaders(file)
  profiles.each do |profile|
    printProfile(file, profile)
  end
  file.close()
end

def getPhoneNo(client, tNo)
  formData = {
      'matid'=>tNo,
      'PageName'=>'VP',
      'PageNo'=>'',
      'pagetype'=>'',
      'placeholder'=>'',
      'userphoneavailable'=>'0',
      'FROMVP'=>'1'
  }
  client.request_headers["Origin"] = "http://profile.telugumatrimony.com"
  client.request_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
  client.request_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
  client.request_headers["Referer"] = "http://profile.telugumatrimony.com/profiledetail/viewprofile.php?id=#{tNo}"
  client.request_headers["X-Requested-With"] = "XMLHttpRequest"
  response = client.post(PhoneUrl, formData)
  node = response.at(".hdtxt1 > .boldtxt")
  if node.blank?
    return nil
  end
  node.inner_text.gsub("91-", '').gsub(/\s+/, '').strip
end

def sendPhotoRequest(client, tNo)
  url = "http://profile.telugumatrimony.com/request/bmrequestfor.php?OID=#{tNo}&RID=1&gaact=REQP&gasrc=VP&FROMVP=1&divId=useracticonsimgs&Var=1&rand=sr15we"
  response = client.get(url)
  node = response.search("div")[3]
  if node.blank?
    return nil
  end
  node.inner_text
end

client = Mechanize.new { |agent|
  agent.user_agent_alias = 'Mac Safari'
  agent.redirect_ok = false
}

client.request_headers = {
    "Accept-Encoding" => "gzip, deflate, sdch",
    "Accept-Language" => "en-US,en;q=0.8",
    "Upgrade-Insecure-Requests" => 1,
    "Accept" => "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer" => LoginUrl,
    "Connection" => "keep-alive"
}
TNos = []
login(client)
scrapeSavedSearch(client, "./Brahmin")
# modifying the request headers cookie
# this is because there is some wierd quotes in the cookies






