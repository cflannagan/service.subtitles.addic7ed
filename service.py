# -*- coding: utf-8 -*- 
# Contents from https://github.com/Diecke/service.subtitles.addicted

import os
import sys
import xbmc
import urllib
import urllib2
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import shutil
import unicodedata
import re
import socket
import string

from BeautifulSoup import BeautifulSoup

__addon__ = xbmcaddon.Addon()
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
__temp__       = xbmc.translatePath( os.path.join( __profile__, 'temp') ).decode("utf-8")

sys.path.append (__resource__)

from Addic7edUtilities import log, languageTranslate, get_language_info

self_host = "http://www.addic7ed.com"
self_release_pattern = re.compile("Version (.+), ([0-9]+).([0-9])+ MBs")
self_release_filename_pattern = re.compile(".*\-(.*)\.")
    
def get_url(url):
  req_headers = {
  'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.A.B.C Safari/525.13',
  'Referer': 'http://www.addic7ed.com'}
  request = urllib2.Request(url, headers=req_headers)
  opener = urllib2.build_opener()
  response = opener.open(request)

  contents = response.read()
  return contents

def append_subtitle(item):
  listitem = xbmcgui.ListItem(label=item['lang']['name'],
                              label2=item['filename'],
                              iconImage=item['rating'],
                              thumbnailImage=item['lang']['2let'])

  listitem.setProperty("sync",  'true' if item["sync"] else 'false')
  listitem.setProperty("hearing_imp", 'true' if item["hearing_imp"] else 'false')

  url = "plugin://%s/?action=download&link=%s&filename=%s" % (__scriptid__,
    item['link'],
    item['filename'])
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False)

def query_TvShow(name, season, episode, langs, file_original_path):
  name = name.lower().replace(" ", "_").replace("$#*!","shit").replace("'","") # need this for $#*! My Dad Says and That 70s show
  searchurl = "%s/serie/%s/%s/%s/addic7ed" %(self_host, name, season, episode)
  filename_string = "%s.S%.2dE%.2d" %(name.replace("_", ".").title(), int(season), int(episode) )
  query(searchurl, langs, file_original_path, filename_string)

def query_Film(name, year, langs, file_original_path):
  name = urllib.quote(name.replace(" ", "_"))
  searchurl = "%s/film/%s_(%s)-Download" %(self_host,name, str(year))
  filename_string = "%s" %(name.replace("_", ".").title() )
  query(searchurl, langs, file_original_path, filename_string)

def query(searchurl, langs, file_original_path, filename_string):
  sublinks = []
  socket.setdefaulttimeout(3)
  request = urllib2.Request(searchurl)
  request.add_header('Pragma', 'no-cache')
  page = urllib2.build_opener().open(request)
  content = page.read()
  content = content.replace("The safer, easier way", "The safer, easier way \" />")
  soup = BeautifulSoup(content)

  file_name = str(os.path.basename(file_original_path)).split("-")[-1].lower()

  for subs in soup("td", {"class":"NewsTitle", "colspan" : "3"}):

    try:
      langs_html = subs.findNext("td", {"class" : "language"})
      fullLanguage = str(langs_html).split('class="language">')[1].split('<a')[0].replace("\n","")
      subteams = self_release_pattern.match(str(subs.contents[1])).groups()[0]

      if (str(subteams.replace("WEB-DL-", "").lower()).find(str(file_name))) > -1:
        hashed = True
      else:
        hashed = False

      try:
        lang = get_language_info(fullLanguage)
      except:
        lang = ""

      statusTD = langs_html.findNext("td")
      status = statusTD.find("b").string.strip()

      linkTD = statusTD.findNext("td")
      link = "%s%s" % (self_host,linkTD.find("a")["href"])

      if(subs.findNext("td", {"class":"newsDate", "colspan" : "2"}).findAll('img', {'title': 'Hearing Impaired'})):
        HI = True
      else:
        HI = False

      if status == "Completed" and (lang['3let'] in langs) :
        sublinks.append({'rating': '0', 'filename': "%s-%s" %(filename_string, subteams ), 'sync': hashed, 'link': link, 'lang': lang, 'hearing_imp': HI})
    except:
      log(__name__, "ERROR IN BS")
      pass

  sublinks.sort(key=lambda x: [not x['sync']])
  log(__name__, "sub='%s'" % (sublinks))

  for s in sublinks:
    append_subtitle(s)

def search_manual(searchstr, languages, filename):
  xbmc.executebuiltin((u'Notification(%s,%s)' % (__scriptname__ , __language__(24000))).encode('utf-8'))
  return False
  search_string = prepare_search_string(searchstr)
  url = self_host + "/search.php?search=" + search_string + '&Submit=Search'
  content, response_url = geturl(url)

  if content is not None:
    return False
    # getallsubs(content, languages, filename)

def search_filename(filename, languages):
  title, year = xbmc.getCleanMovieTitle(filename)
  log(__name__, "clean title: \"%s\" (%s)" % (title, year))
  try:
    yearval = int(year)
  except ValueError:
    yearval = 0
  if title and yearval > 1900:
    query_Film(title, year, item['3let_language'], filename)
  else:
    match = re.search(r'\WS(?P<season>\d\d)E(?P<episode>\d\d)', title, flags=re.IGNORECASE)
    if match is not None:
      tvshow = string.strip(title[:match.start('season')-1])
      season = string.lstrip(match.group('season'), '0')
      episode = string.lstrip(match.group('episode'), '0')
      query_TvShow(tvshow, season, episode, item['3let_language'], filename)
    else:
      search_manual(filename, item['3let_language'], filename)


def Search(item):
  filename = os.path.splitext(os.path.basename(item['file_original_path']))[0]
  log(__name__, "Search_addic7ed='%s', filename='%s', addon_version=%s" % (item, filename, __version__))

  if item['mansearch']:
    search_manual(item['mansearchstr'], item['3let_language'], filename)
  elif item['tvshow']:
    query_TvShow(item['tvshow'], item['season'], item['episode'], item['3let_language'], filename)
  elif item['title'] and item['year']:
    query_Film(item['title'], item['year'], item['3let_language'], filename)
  else:
    search_filename(filename, item['3let_language'])

  
def download(link):
  subtitle_list = []

  if xbmcvfs.exists(__temp__):
    shutil.rmtree(__temp__)
  xbmcvfs.mkdirs(__temp__)

  file = os.path.join(__temp__, "addic7ed.srt")

  f = get_url(link)

  local_file_handle = open(file, "wb")
  local_file_handle.write(f)
  local_file_handle.close()

  subtitle_list.append(file)

  if len(subtitle_list) == 0:
    if search_string:
      xbmc.executebuiltin((u'Notification(%s,%s)' % (__scriptname__ , __language__(32002))).encode('utf-8'))
    else:
      xbmc.executebuiltin((u'Notification(%s,%s)' % (__scriptname__ , __language__(32003))).encode('utf-8'))

  return subtitle_list


def normalizeString(str):
  return unicodedata.normalize(
      'NFKD', unicode(unicode(str, 'utf-8'))
  ).encode('ascii', 'ignore')


def get_params():
  param = {}
  paramstring = sys.argv[2]
  if len(paramstring) >= 2:
    params = paramstring
    cleanedparams = params.replace('?', '')
    if (params[len(params) - 1] == '/'):
      params = params[0:len(params) - 2]
    pairsofparams = cleanedparams.split('&')
    param = {}
    for i in range(len(pairsofparams)):
      splitparams = pairsofparams[i].split('=')
      if (len(splitparams)) == 2:
        param[splitparams[0]] = splitparams[1]

  return param


params = get_params()

if params['action'] == 'search' or params['action'] == 'manualsearch':
  item = {}
  item['temp'] = False
  item['rar'] = False
  item['mansearch'] = False
  item['year'] = xbmc.getInfoLabel("VideoPlayer.Year")                             # Year
  item['season'] = str(xbmc.getInfoLabel("VideoPlayer.Season"))                    # Season
  item['episode'] = str(xbmc.getInfoLabel("VideoPlayer.Episode"))                  # Episode
  item['tvshow'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))   # Show
  item['title'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle"))  # try to get original title
  item['file_original_path'] = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path
  item['3let_language'] = []

  if 'searchstring' in params:
    item['mansearch'] = True
    item['mansearchstr'] = params['searchstring']

  for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
    item['3let_language'].append(xbmc.convertLanguage(lang, xbmc.ISO_639_2))

  if item['title'] == "":
    item['title'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.Title"))      # no original title, get just Title

  if item['episode'].lower().find("s") > -1:                                      # Check if season is "Special"
    item['season'] = "0"                                                          #
    item['episode'] = item['episode'][-1:]

  if item['file_original_path'].find("http") > -1:
    item['temp'] = True

  elif item['file_original_path'].find("rar://") > -1:
    item['rar'] = True
    item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

  elif item['file_original_path'].find("stack://") > -1:
    stackPath = item['file_original_path'].split(" , ")
    item['file_original_path'] = stackPath[0][8:]

  Search(item)

elif params['action'] == 'download':
  subs = download(params["link"])
  for sub in subs:
    listitem = xbmcgui.ListItem(label=sub)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=listitem, isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))  # send end of directory to XBMC