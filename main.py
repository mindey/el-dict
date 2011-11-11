#-coding- utf-8
import cgi
import datetime
import urllib
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

admins = ['yoshikomc', 'm.indriunas@universians.org']

class Iword(db.Model):
  """Models an individual Iword entry with a token, sense id (sid), sense clue (sclue), frequency (freq)."""
  token = db.StringProperty()
  mapto = db.ListProperty(db.Key)
  sid = db.IntegerProperty()
  sclue = db.StringProperty()
  freq = db.IntegerProperty()
  link = db.StringProperty()

def iword_key(lang=None):
  """Constructs a datastore key for a Iword entity with lang."""
  return db.Key.from_path('Iword', lang or 'en')

def elset(word):
  """Sorts a string."""
  return ''.join(sorted(word))

class MainPage(webapp.RequestHandler): # When opening the website, and starting to search...
  def get(self):
    # Collecting GET variables
    lang1 = self.request.get('f')
    lang2 = self.request.get('t')
    word = self.request.get('w')

    # Getting current user:
    user = users.get_current_user()


    if lang1 == 'el':
      spacer1 = ' '
    else:
      spacer1 = ''

    if lang2 == 'el':
      spacer2 = ' '
    else:
      spacer2 = ''

    # Needed for searching EL words
    if lang1 == 'el':
      word = elset(word)

    # Defining the lang1 and lang2 if they happen to be undefined.
    if lang1:
      lang1 = self.request.get('f').lower()
      embed1 = '<input type="hidden" name="f" value="%s">' % lang1
    else:
      lang1 = 'en'
      embed1 = ''
    if lang2:
      lang2 = self.request.get('t').lower()
      embed2 = '<input type="hidden" name="t" value="%s">' % lang2
    else:
      lang2 = 'el'
      embed2 = ''

    #Defining the options. These options should be made from a list of languages.
    #Only the selection of these options should change. By making them the first ones.
    languages = ['el', 'en', 'ja', 'lt', 'zh', 'es', 'ru', 'fr', 'fi']
    n = len(languages)
    import copy
    remain1 = copy.deepcopy(languages)
    remain2 = copy.deepcopy(languages)
    a = remain1.pop(remain1.index(lang1))
    b = remain2.pop(remain2.index(lang2))
    option1 = '<option>%s</option>'*n % tuple([lang1]+remain1)
    option2 = '<option>%s</option>'*n % tuple([lang2]+remain2)

    iwords = db.GqlQuery("SELECT * "
                         "FROM Iword "
                         "WHERE ANCESTOR IS :1 AND token = :2 "
                         "ORDER BY freq DESC LIMIT 10",
                         iword_key(lang1), word)

    self.response.out.write("""<html>
  <head>
      <link type="text/css" rel="stylesheet" href="/stylesheets/main.css" />
  <script type="text/javascript"
   src="http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js"></script>
  <script type="text/javascript" src="stylesheets/map.js"></script>
  </head>
  <body>
    <form action="/?w=%s" method="get" style='display:inline;'>
    <div class="fieldHolder"><input type="text" name="w" class="%sInput"> <input type="submit" value="Search" class="searchButton"> </div>
    %s
    %s
    </form>
    <form style='display:inline;'>
    <div class="fieldHolder">
    From <select name="f" class="selectInput">%s</select>
    To <select name="t" class="selectInput">%s</select>
    <input type="submit" value="switch" class="switchInput">
    </div>
    </form>
    <hr>""" % (word, lang1, embed1, embed2, option1, option2))

    if word != "*":
      if len(word) == 0:
#       self.response.out.write('<a href="/?w=*&f=%s&t=%s">see all words in <font color="red">%s</font></a>' % (lang1, lang2, lang1))
        self.response.out.write("""<font size="-1">Try typing "orange<font color="red">1</font> != orange<font color="red">2</font>":</font> """)
        self.response.out.write('<br><textarea id="from" cols="40" rows="7"></textarea> <textarea id="to" cols="40" rows="7"></textarea></hr>')
        if not user:
          greeting = ("<br><a href=\"%s\">Sign in or register</a>." % users.create_login_url("/"))
        else:
          greeting = ("<br>Welcome, %s! (<a href=\"%s\">sign out</a>)" % (user.nickname(), users.create_logout_url("/")))
        self.response.out.write('<br>%s<br>' % greeting)
    else:
      iwords = db.GqlQuery("SELECT * "
                           "FROM Iword "
                           "WHERE ANCESTOR IS :1 "
                           "ORDER BY freq DESC LIMIT 1000",
                           iword_key(lang1))
#     iwords = Iword.all()
#     iwords.filter("ANCESTOR IS", iword_key(lang1))


    for iword in iwords:
      if iword.link is not None:
        source = '<a href="%s" target="_blank">source</a>' % iword.link
      else:
        source = ''
      self.response.out.write('<blockquote><span class="%s">%s%s</span><font color="red">%s</font> (%s) <font size="-1"><a href="/edt?k=%s&lang=%s&t=%s">edit..</a> %s</font>' %
                              (lang1, cgi.escape(iword.token), spacer1, iword.sid, cgi.escape(iword.sclue), str(iword.key()), lang1, lang2, source) )

      self.response.out.write('<blockquote>')


      #<HERE WE'LL BE PRINTING OUT TRANSLATIONS>
      if iword.mapto:
        items = Iword.get(iword.mapto)
        for item in items:
          if item.key().parent() == iword_key(lang2):   # By changing the language, we can change output.
            self.response.out.write("""<span class="%s">%s </span><font color="red">%s</font></br> """ % (lang2, item.token, str(item.sid)))
      #/

      self.response.out.write('<font size="-1"><a href="/map?k=%s&f=%s&t=%s">map to..</a></font></blockquote>' % (str(iword.key()), lang1, lang2))
      self.response.out.write('</blockquote>')
    
    if word:
      appendix = ' FOR %s' % word
    else:
      appendix = ''

    if word:
      if word != '*':
        self.response.out.write("""
    <hr>
    <form>
    <input type="button" value="ADD NEW SENSE%s" onclick="window.location.href='new?w=%s&lang=%s'">
    </form>
  </body>
</html>""" % (appendix, word, lang1))

class AddSense(webapp.RequestHandler):  # When clicking on the button "Add New Sense for word ...", we are forwarded to this page.
  def get(self):
    # Getting current user:
    user = users.get_current_user()

    # INPUT
    lang=self.request.get('lang')
    word=self.request.get('w')
    if lang == 'el':
      word = elset(word)
    iwords = db.GqlQuery("SELECT * "
                         "FROM Iword "
                         "WHERE ANCESTOR IS :1 AND token = :2 "
                         "ORDER BY freq DESC LIMIT 100",
                         iword_key(lang), word)

    # OUTPUT
   #if user:
   #  if user.nickname() in admins:
    self.response.out.write("""<html>
  <head>
      <link type="text/css" rel="stylesheet" href="/stylesheets/main.css" />
  </head>
  <body>
  <a href="/?f=%s"><<</a>
  <blockquote>""" % lang)
    self.response.out.write('<font color="red">%s</font>: %s' % (lang, word))
    for iword in iwords:
      self.response.out.write('<blockquote>%s. <span class="%s">%s </span><font color="red">%s</font> (%s)</blockquote>' %
                              (iword.key().id(), lang, cgi.escape(iword.token), iword.sid, cgi.escape(iword.sclue)) )

    self.response.out.write("""
          <form action="/add?lang=%s" method="post">
            <div class="fieldHolder">Word: <input type="text" name="token" class="%sInput" value="%s" readonly></div>
            <div>Sense: <input type="text" name="sense_clue"></div>
            <div>Source: <input type="text" name="link"></div>
            <div><input type="submit" value="Add New Entry"></div>

          </form>
          </blockquote>
        </body>
      </html>""" % (lang, lang, word))

class AddWord(webapp.RequestHandler):  # This page is executed, when a user clicks button "Add New Entry", after having filled out the New Entry Form in the AddSense page.
  def post(self):
    # Getting current user:
    user = users.get_current_user()

    #INPUT
    lang = self.request.get('lang')
    link=self.request.get('link')
    iword = Iword(parent=iword_key(lang))
    iword.token = self.request.get('token')
    
    if user:
      if user.nickname() in admins:
        #[find iword with of same token, and add 1 to maximum sid
        q = db.GqlQuery("SELECT * " +
                        "FROM Iword " +
                        "WHERE ANCESTOR IS :1 AND token = :2 " +
                        "ORDER BY sid DESC",
                        iword_key(lang), iword.token)
        r = q.fetch(1)
        if r:
            iword.sid = r[0].sid+1
        else:
            iword.sid = 1
        #/find]
        iword.sclue = self.request.get('sense_clue')
        iword.freq = 1
        iword.link = link
        iword.put()

        # OUTPUT
#   self.redirect('/new?w=%s&lang=%s' % (iword.token, lang)) # SINCE THE URLLIB.URLENCODE doesn't work properly...
        self.redirect('/?f=%s' % (lang))
    else:
        self.response.out.write('Sorry, but you do not have rights of adding new senses. You can however, suggest a new sense.')

class AddMap(webapp.RequestHandler):  # This page is executed, when a user clicks link "map to..."
  def get(self):
    #TAKING THE GET VARIABLES
    mapwhat = self.request.get('k')
    lang1 = self.request.get('f')
    lang2 = self.request.get('t') #[target language]

    if lang1 == 'el':
      spacer1 = ' '
    else:
      spacer1 = ''

    if lang2 == 'el':
      spacer2 = ' '
    else:
      spacer2 = ''

    # UPDATING THE MAPPING IF NEEDED
#   if there are i-number-variables in get list:
#     for each number-variable:
#       append its key to the k-key mapto, if it is not yet there, on both sides
    i_starting_variable_ids = []
    for var in self.request.arguments():
      if var[0] in 'i':
        if var[1:].isdigit():
          i_starting_variable_ids.append(var[1:])
    for i in i_starting_variable_ids:
      iKey = db.Key.from_path(u'Iword', lang2, u'Iword', long(i)) # Fancy way of getting the key from ID
      mapit = Iword.get(iKey)
      target = Iword.get(mapwhat)
      #-- Map the mapit (source) to target --
      if mapit.key() not in target.mapto:
        target.mapto.append(mapit.key())
        target.put()
      #-- Map the target to mapit (source) --
      if target.key() not in mapit.mapto:
        mapit.mapto.append(target.key())
        mapit.put()

#   if there are d-number-variables in get list:
#     for each d-number-variable:
#       remove its key from the k-key mapto, if it is there, on both sides
    d_starting_variable_ids = []
    for var in self.request.arguments():
      if var[0] in 'd':
        if var[1:].isdigit():
          d_starting_variable_ids.append(var[1:])

    for d in d_starting_variable_ids:
      dKey = db.Key.from_path(u'Iword', lang2, u'Iword', long(d))
      unmapit = Iword.get(dKey)
      target = Iword.get(mapwhat)
      #-- Unmap the mapit (source) from target
      if unmapit.key() in target.mapto:
        z = target.mapto.index(unmapit.key())
        x = target.mapto.pop(z)
        target.put()
      #-- Unmap the target from mapit (source) 
      if target.key() in unmapit.mapto:
        z = unmapit.mapto.index(target.key())
        y = unmapit.mapto.pop(z)
        unmapit.put()
         

#   beverage = db.GqlQuery("SELECT * "
#                          "FROM Iword "
#                          "WHERE ANCESTOR IS :1 AND token = :2 "
#                          "ORDER BY freq DESC LIMIT 1",
#                          iword_key('en'), 'beverage').fetch(1)[0]

#   hI = Iword.gql("WHERE token = 'hI' AND sid = 1 LIMIT 1").get()
#   beverage.mapto.append(hI.key())
#   beverage.put()

    #REDISPLAY WHAT WE ARE MAPPING
    r = Iword.get(mapwhat)
    self.response.out.write("""<html>
  <head>
      <link type="text/css" rel="stylesheet" href="/stylesheets/main.css" />
  </head>
  <body>
  <a href="/"><<</a>
  """)

    self.response.out.write("""<blockquote><span class="%s">%s%s</span><font color='red'>%s</font> (%s)""" % (lang1, r.token, spacer1, r.sid, r.sclue))

    #PREPARING THE FORM, and possibility to search for words in various languages
    self.response.out.write("""
                            <blockquote>
                            <form action="/map" method="get">
                             <input type="hidden" name="k" value="%s">
                             <input type="hidden" name="f" value="%s">
                             <input type="hidden" name="t" value="%s">
                            <hr color="orange">""" % (mapwhat, lang1, lang2))
    for item in r.mapto:
        iw = Iword.get(item)
        self.response.out.write("""<input type="checkbox" name="d%s"><span class="%s">%s%s</span><font color="red">%s</font><br>""" % (iw.key().id(), lang2, iw.token, spacer2, str(iw.sid)) )

    self.response.out.write("""
                            <hr color="orange">
                            <div class="fieldHolder">
                                <input type="submit" value="Unmap" class="searchButton">
                            </div>
                            </form>""")
    self.response.out.write("""
                            <form action="/map" method="get">
                            <div class="fieldHolder">
                             <input type="text" name="w" class="%sInput">
                             <input type="submit" value="Search" class="elSearchButton">
                             <input type="hidden" name="k" value="%s">
                             <input type="hidden" name="f" value="%s">
                             <input type="hidden" name="t" value="%s">
                            </div>
                            <hr color="orange">
                            """ % (lang2, mapwhat, lang1, lang2)) 

          ### SEARCH
    word = self.request.get('w')
    if lang2 == 'el':
      word = elset(word)

    iwords = db.GqlQuery("SELECT * "
                         "FROM Iword "
                         "WHERE ANCESTOR IS :1 AND token = :2 "
                         "ORDER BY freq DESC LIMIT 1000",
                         iword_key(lang2), word)
           ### /
    
    for iword in iwords:
      if iword.key() in r.mapto:
        value = 'checked'
      else:
        value = ''
      self.response.out.write("""<input type="checkbox" name="i%s" %s><span class="%s">%s </span><font color="red">%s</font> (%s)<br>""" % (iword.key().id(), value, lang2, iword.token, str(iword.sid), iword.sclue))

    self.response.out.write("""
                            <hr color="orange">
                            <input type="submit" value="Map" class="searchButton">
                            </blockquote>
                            </blockquote>
                            </form>
                            """)

    self.response.out.write("""</body></html>""")

    #APPENDING NEW Keys as references, as described http://code.google.com/appengine/articles/modeling.html (List of Keys)
    # SINCE THIS HAS TO BE DONE _BEFORE_ DISPLAYING THE FORM,
    # WE DO IT IN THE BEGINNING OF THIS METHOD


    
class EditSense(webapp.RequestHandler):  # This page is executed, when a user clicks link "map to..."
  def get(self):
    # GET THE VARS
    lang = self.request.get('lang')
    lang2 = self.request.get('t')
    token = self.request.get('token')
    sclue = self.request.get('sclue')
    sid = self.request.get('sid')
    link = self.request.get('link')
    key = self.request.get('k')
    r = Iword.get(key)

    # UPDATE THE WORD, IF OKAY
    if (token):
      r.token = token
      # Make a check, that there wouldn't be duplicate sids
      r.sid = int(sid)
      r.sclue = sclue
      r.link = link
      r.put()

    # REDISPLAY THE WORD
    self.response.out.write("""<html>
  <head>
      <link type="text/css" rel="stylesheet" href="/stylesheets/main.css" />
  </head>
  <body>
  <a href="/?w=*&f=%s&t=%s"><<</a>
  <blockquote>
  <form action="/edt" method="get">
  """ % (lang, lang2))

    self.response.out.write("""
    Word: <input type="text" class="%sInput" name="token" value="%s"> <br>
    Sid: <input type="text" name="sid" value="%s"> <br>
    Sense Clue: <input type="text" name="sclue" value="%s"> <br>
    Source: <input type="text" name="link" value="%s" size="50"> <br>
    <input type="hidden" name="k" value="%s">
    <input type="hidden" name="lang" value="%s">
    <input type="submit" value="Save">
    </form>
    </blockquote>
    </body></html>""" % (lang, r.token, r.sid, r.sclue, r.link, key, lang))




application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/new', AddSense),
  ('/add', AddWord),
  ('/map', AddMap),
  ('/edt', EditSense),
], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == '__main__':
  main()
