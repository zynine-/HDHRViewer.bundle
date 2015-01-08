#HDHR Viewer by zynine (Zheng Yang Tay)

import time
import string
from datetime import datetime

PREFIX = "/video/HDHRViewer"
NAME = "HDHR Viewer"
ART = "art-default.png"
ICON = "icon-default.png"
VERSION = "0.5"	
TIMEOUT = 5					# XML Timeout (s)
CACHETIME = 60				# Cache Time (s)
DURATION = 14400000			# Duration for Transcoder
MAX_SIZE = 20971520			# [Bytes] 20971520 = 20MB Default: 5242880 (5MB)
PAGINATION = 20				# Number of listing per page. (not used)

def Start():
	ObjectContainer.title1 = NAME
	DirectoryItem.thumb = R(ICON)
    
@handler(PREFIX, NAME, ICON, ART)
def MainMenu():

	Log.Debug(Core.bundle_path)
	
	GetInfo()
	
	oc = ObjectContainer(title1=NAME,no_cache=True)
	
	#v0.4 Check IP
	try:
		xml_channellineup_url = "http://"+Prefs["hdhomerun_ip"]+"/lineup.xml"
		xml_channellineup = XML.ElementFromURL(xml_channellineup_url,timeout=TIMEOUT,cacheTime=CACHETIME)
	except:
		xml_channellineup = None
		oc.add(DirectoryObject(key = Callback(ErrorMessage, message = "HDHomeRun: Not detected. Check IP"), title = "Error: HDHomeRun", thumb = R("icon-error.png")))
		Log.Error("HDHomeRun: Not detected. Check IP")
	
	try:
		#v0.4 Custom Lineup
		if Prefs["custom_lineup_enable"]:
			xml_channellineup = XML.ElementFromString(Resource.Load(Prefs["custom_lineup"]))
		else:
			xml_channellineup_url = "http://"+Prefs["hdhomerun_ip"]+"/lineup.xml"
			xml_channellineup = XML.ElementFromURL(xml_channellineup_url,timeout=TIMEOUT,cacheTime=CACHETIME)
	except:
		xml_channellineup = None
		oc.add(DirectoryObject(key = Callback(ErrorMessage, message = "HDHomeRun: Error loading lineup.xml"), title = "Error: HDHomeRun", thumb = R("icon-error.png")))
		Log.Error("HDHomeRun: Error loading lineup.xml")
	
	#If line up exist, add favorite and subscribed.
	if xml_channellineup != None:
		#Favorites
		oc.add(ChannelCategory(title="Favorites",xpath="//Program[Tags='favorite']",thumb=R("icon-fav.png"),program_info=True,xml_channellineup=xml_channellineup))
	
		#Subscribed	
		oc.add(ChannelCategory(title="Subscribed",xpath="//Program",thumb=R("icon-subscribed.png"),program_info=True,xml_channellineup=xml_channellineup))
		
	#Check XMLTV
	if not XMLTVCheckOK() and Prefs["xmltv_enable"]:
		oc.add(DirectoryObject(key = Callback(ErrorMessage, message = "ProgramInfo: Failed to load"), title = "Error: ProgramInfo", thumb = R("icon-error.png")))
			
	#Settings
	oc.add(PrefsObject(title='Settings', thumb=R('icon-settings.png')))

	return oc

@route(PREFIX + "/submenu/{title}")
def SubMenu(title,xpath,program_info):

	oc = ObjectContainer(title2=title,no_cache=True)

	xmltv_location = None
	xmltv = None
		
	if Prefs["xmltv_enable"]:
		try:
			xmltv_location = Resource.Load(Prefs["xmltv"])
			xmltv = XML.ElementFromString(xmltv_location,max_size=MAX_SIZE)
		except:
			Log.Error("submenu/XMLTV: Error loading xmltv.xml")
			program_info=False
	else:
		program_info=False
	
	#v0.4 Custom Lineup
	if Prefs["custom_lineup_enable"]:
		xml_channellineup = XML.ElementFromString(Resource.Load(Prefs["custom_lineup"]))
	else:
		xml_channellineup_url = "http://"+Prefs["hdhomerun_ip"]+"/lineup.xml"
		xml_channellineup = XML.ElementFromURL(xml_channellineup_url,timeout=TIMEOUT,cacheTime=CACHETIME)
	

	#Get channels from lineup.xml
	channels = xml_channellineup.xpath(xpath)
	
	for element in channels:
		GuideNumber = element.xpath("GuideNumber")[0].text
		GuideName = element.xpath("GuideName")[0].text
		
		#v0.4
		if GuideName is None:
			GuideName = ""
				
		Log.Debug(GuideNumber+":"+GuideName)
		
		#v0.4 modification to filename in case of blank name
		if GuideName == "" or Prefs["channellogo"] == "number":
			filename = "logo-"+makeSafeFilename(GuideNumber)+".png"
		else:
			filename = "logo-"+makeSafeFilename(GuideName)+".png"
			
		Log.Debug("thumbnail:"+filename)
	
		StreamURL = "http://"+Prefs["hdhomerun_ip"]+":5004/"+Prefs["hdhomerun_tuner"]+"/v" + GuideNumber
		
		Thumb = R(filename)
		
		#PROGRAM INFO START
		#Default Episode Info
		ep_title = " "
		ep_desc = " "
		ep_time = " "
		ep_info = " "
		ep_next = " "
		channelid = " "
		c_title = " "
		ep_subtitle = " "
		
		#Show TV Info
		if program_info and xmltv_location!=None:
			
			#System Time
			c_time = time.strftime("%Y%m%d%H%M%S")
	
			#Get Channel using Channel/Guide Number or Name
			if Prefs["xmltv_match"]=="number":
				channeldata = xmltv.xpath("//channel[display-name="+GuideNumber+"]")
			else:
				channeldata = xmltv.xpath("//channel[display-name='"+GuideName+"']")
			
			#If Channel exist
			if len(channeldata)>0:
				#Get ChannelID
				channelid = channeldata[0].xpath('@id')[0]
				
				#Get Episodes based on ChannelID
				episodes = xmltv.xpath("//programme[@channel = '" + channelid + "']")
				
				#If Episodes exist
				if len(episodes)>0:
					#Future Episodes Counter
					i = 0
					for episode in episodes:
						#Trim start and stop times from episodes
						ep_starttime = str(episode.xpath('@start'))[2:16]
						ep_stoptime = str(episode.xpath('@stop'))[2:16]
						
						#Current Episode
						if ep_starttime<c_time and c_time<ep_stoptime:
							i=i+1
							ep_time = datetime.strptime(ep_starttime,"%Y%m%d%H%M%S").strftime("%I:%M %p")
							try:
								ep_title = " - "+episode.xpath("title")[0].text
							except:
								ep_title = ""
							try:
								ep_subtitle = " - "+episode.xpath("sub-title")[0].text
							except:
								ep_subtitle = ""
							#only mc2xml seems to give desc
							try:
								ep_desc = " - "+episode.xpath("desc")[0].text
							except:
								ep_desc = ""
							ep_info = ep_time+ep_title+ep_subtitle+ep_desc+" \r\n"
							c_title=ep_title
							c_subtitle=ep_subtitle
							
						#Next Episodes
						if ep_starttime>c_time:
							i=i+1
							ep_time = datetime.strptime(ep_starttime,"%Y%m%d%H%M%S").strftime("%I:%M %p")
							try:
								ep_title = " - "+episode.xpath("title")[0].text
							except:
								ep_title = ""
							try:
								ep_subtitle = " - "+episode.xpath("sub-title")[0].text
							except:
								ep_subtitle = ""
							#only mc2xml seems to give desc
							try:
								ep_desc = " - "+episode.xpath("desc")[0].text
							except:
								ep_desc = ""
							ep_next = ep_next+ep_time+ep_title+ep_subtitle+ep_desc+" \r\n"
						
						#Episode Limit
						if i>=int(Prefs["xmltv_maxlist"]):
							break
							
						ep_title=""
						ep_desc=""
						ep_time=""

		Title = GuideNumber + " - " + GuideName
		
		if c_title!=" ":
			Title = Title + c_title + c_subtitle
			
		#PROGRAM INFO END
		
		oc.add(CreateVO(url=StreamURL, title=Title, tagline=ep_info, summary=ep_info+ep_next, thumb=Thumb))
	return oc
	
@route(PREFIX + "/CreateVO")
def CreateVO(url, title, tagline, summary, thumb, include_container=False):
	#v0.4 auto transcode based off lazybones code with some modifications
	#v0.5 transcode rewritten and corrected.
	
	if Prefs["transcode"]=="auto":
		#AUTO TRANSCODE
		vo = VideoClipObject(
		rating_key = url,
		key = Callback(CreateVO, url=url, title=title, tagline=tagline, summary=summary, thumb=thumb, include_container=True),
		title = title,
		summary = summary,
		#Plex.tv & Roku3
		tagline = tagline,
		source_title = tagline,
		#without duration, transcoding will not work... 
		duration = DURATION,
		thumb = thumb,
		items = [	
			MediaObject(
				parts = [PartObject(key=(url+"?transcode=heavy"))],
				container = "mpegts",
				video_resolution = 1080,
				bitrate = 20000,
				video_codec = VideoCodec.H264,
				audio_codec = "AC3",
				optimized_for_streaming = True
			),
			MediaObject(
				parts = [PartObject(key=(url+"?transcode=mobile"))],
				container = "mpegts",
				video_resolution = 720,
				bitrate = 7000,
				video_codec = VideoCodec.H264,
				audio_codec = "AC3",
				optimized_for_streaming = True
			),
			MediaObject(
				parts = [PartObject(key=(url+"?transcode=internet480"))],
				container = "mpegts",
				video_resolution = 480,
				bitrate = 3000,
				video_codec = VideoCodec.H264,
				audio_codec = "AC3",
				optimized_for_streaming = True
			),
			MediaObject(
				parts = [PartObject(key=(url+"?transcode=internet240"))],
				container = "mpegts",
				video_resolution = 240,
				bitrate = 1000,
				video_codec = VideoCodec.H264,
				audio_codec = "AC3",
				optimized_for_streaming = True
			),
		]
		)
	elif Prefs["transcode"]=="none":
		vo = VideoClipObject(
		rating_key = url,
		key = Callback(CreateVO, url=url, title=title, tagline=tagline, summary=summary, thumb=thumb, include_container=True),
		title = title,
		summary = summary,
		#Plex.tv & Roku3
		tagline = tagline,
		source_title = tagline,
		#without duration, transcoding will not work... 
		duration = DURATION,
		thumb = thumb,
		items = [	
			MediaObject(
				parts = [PartObject(key=(url))],
				container = "mpegts",
				video_resolution = 1080,
				bitrate = 20000,
				video_codec = "mpeg2video",
				audio_codec = "AC3",
				optimized_for_streaming = True
			)
		]	
		)
	else:
		#force transcode reintroduced in v0.5
		Log.Debug(url+"?transcode="+Prefs["transcode"])
		vo = VideoClipObject(
		rating_key = url,
		key = Callback(CreateVO, url=url, title=title, tagline=tagline, summary=summary, thumb=thumb, include_container=True),
		title = title,
		summary = summary,
		#Plex.tv & Roku3
		tagline = tagline,
		source_title = tagline,
		#without duration, transcoding will not work... 
		duration = DURATION,
		thumb = thumb,
		items = [	
			MediaObject(
				parts = [PartObject(key=(url+"?transcode="+Prefs["transcode"]))],
				container = "mpegts",
				video_codec = VideoCodec.H264,
				audio_codec = "AC3",
				optimized_for_streaming = True
			)
		]	
		)
	


	if include_container:
		return ObjectContainer(objects=[vo])
	else:
		return vo
		
@route(PREFIX + "/error/{message}")
def ErrorMessage(message):
	return ObjectContainer(header="Error", message=message)

@route(PREFIX + "/channelcat/{title}")
def ChannelCategory(title,xpath,program_info,xml_channellineup,thumb=R("icon-default.png")):
	xml_channellineup=xml_channellineup
	channels = xml_channellineup.xpath(xpath)
	
	#v0.3 20140530beta2 firmware favorite fix
	if xpath=="//Program[Tags='favorite']" and len(channels)==0:
		xpath = "//Program[Favorite='1']"
		channels = xml_channellineup.xpath(xpath)
		
	return DirectoryObject(key = Callback(SubMenu, title=title, xpath=xpath, program_info=program_info), title = title + " ("+str(len(channels))+")", thumb = thumb)

#future function
@route(PREFIX + "/XMLTVCheck")
def XMLTVCheckOK():
	Log.Debug("XMLTVCheck")
	try:
		xmltv_location = Resource.Load(Prefs["xmltv"])
		xmltv = XML.ElementFromString(xmltv_location,max_size=MAX_SIZE)
		Log.Debug("XMLTV-size:"+str(len(xmltv_location)/1024)+"kb")
		generator=xmltv.xpath("//tv/@generator-info-name")[0]
		Log.Debug("XMLTV-generator:"+generator)
		source=xmltv.xpath("//tv/@source-info-name")[0]
		Log.Debug("XMLTV-source:"+source)
		return True
	except:
		xmltvtype = "None"
		Log.Error("XMLTVCheck: Fail")
		return False
			
@route(PREFIX + "/GetInfo")
def GetInfo():
	Log.Debug(str(Request.Headers))
	Log.Debug("HDHRViewerVersion:"+VERSION)
	Log.Debug("PlatformOS:"+Platform.OS)
	Log.Debug("PlatformCPU:"+Platform.CPU)
	Log.Debug("PlatformHasSilverlight:"+str(Platform.HasSilverlight))
	Log.Debug("ClientPlatform:"+str(Client.Platform))
	Log.Debug("ClientPlatform:"+str(Client.Protocols))
	Log.Debug("SettingsHDHomeRunIP:"+str(Prefs["hdhomerun_ip"]))
	Log.Debug("SettingsXMLTVEnable:"+str(Prefs["xmltv_enable"]))
	Log.Debug("SettingsXMLTV:"+str(Prefs["xmltv"]))
	Log.Debug("SettingsCustomLineupEnable:"+str(Prefs["custom_lineup_enable"]))
	Log.Debug("SettingsCustomLineup:"+str(Prefs["custom_lineup"]))
	Log.Debug("SettingsTranscode:"+str(Prefs["transcode"]))
	
	
def makeSafeFilename(inputFilename):     
	try:
		safechars = string.letters + string.digits + "-_."
		return filter(lambda c: c in safechars, inputFilename)
	except:
		return ""
	pass