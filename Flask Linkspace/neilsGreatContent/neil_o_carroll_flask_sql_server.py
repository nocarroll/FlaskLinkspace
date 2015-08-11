from flask import Flask, render_template, redirect, url_for, request, session, make_response
import pymysql
import datetime


app = Flask(__name__)

"""




flask server with SQL by Neil O'Carroll
19/02/2015

goals:
        > store posts, comments in a database
        > allow login of set userbase
        > use sessions to handle user across pages
        > allows user to log out any time
        > change presentation of pages for non-logged in users
        > return queries from database with most recent first

notes:
        > doesn't support registering of new users
        > doesn't count comments
        > prevents injection attacks (as far as I was willing to test)



for testing:
        > log in with-----------username: glenn
                                password: strong

        


"""

def openConnection():
        conn = pymysql.connect(host='mysql.scss.tcd.ie', user='REMOVED', passwd='REMOVED', db='REMOVED')
        cur = conn.cursor()
        return cur


#open connection
def openConnectionAlt():
        conn = pymysql.connect(host='mysql.scss.tcd.ie', user='REMOVED', passwd='REMOVED', db='REMOVED')
        cur = conn.cursor()
        return cur, conn

#get all the posts and their details for the front page        
def lookUpPosts():
        cur, conn = openConnectionAlt()
        cur.execute("SELECT * FROM TableOfPosts ORDER BY timestamp DESC")
        postData = []
        for r in range(int(cur.rowcount)):
                row = cur.fetchone()
                postData.append(row)
        
        cur.close()
        conn.close()
        return postData
        # this is the way to isolate data from the lookUpPosts() function

        

# return a tuple of the post details of the order (postID, url, title, description, user, time)
def getPostDetails(postID):
        cur, conn = openConnectionAlt()
        cur.execute("SELECT * FROM TableOfPosts WHERE postID = %s" %postID )
        postDetailsTuple = None
        if int(cur.rowcount) == 1:
                postDetailsTuple = cur.fetchone()
        else:
                postDetailsTuple = (None)


        cur.close()
        conn.close()
        #this function will be added in the jinja template to format the datetime object
        #postDetailsTuple[5].strftime("%a %b %d %Y at %H:%M:%S")
        return postDetailsTuple


#check if the username and password is correct
def checkUser(username, password):
        print(username)
        cur, conn = openConnectionAlt()
        cur.execute("SELECT * FROM TableOfUsers")

        for r in range(int(cur.rowcount)):
                tup = cur.fetchone()
                if tup[1] == username and tup[2] == password:

                        cur.close()
                        conn.close()
                        return True
                        
        return False

def getCommentsForPost(postID):
        cur, conn = openConnectionAlt()
        cur.execute("SELECT * FROM TableOfComments WHERE postID = %s ORDER BY timestamp DESC" %postID )
        # the request has the comments in tuple form
        # templates take a list of comments so they must be converted 
        commentTuples = []
        commentThread = []
        for r in range(int(cur.rowcount)):
                row = cur.fetchone()
                commentTuples.append(row)
        
        cur.close()
        conn.close()
        
        # this converts comment tuple list to a list of comma separated strings
        for r in range(int(len(commentTuples))):
                commentThread.append(commentTuples[r])
        return commentThread

def addCommentToDb(theComment, theCommenter, thePostID):
        cur, conn = openConnectionAlt()
        # cleanse that stuff
        escapedComment = conn.escape(theComment)
        escapedUser = conn.escape(theCommenter)
        escapedID = conn.escape(thePostID)
        cur.execute("INSERT INTO TableOfComments SET comment = %s, username = %s, postID = %s ;" %(escapedComment, escapedUser, escapedID))

        conn.commit()
        cur.close()
        conn.close()

def addLinkToDb(someUrl, title, info, userName):
        cur, conn = openConnectionAlt()
        # cleanse that stuff
        escUrl = conn.escape(someUrl)
        escTitle = conn.escape(title)
        escInfo = conn.escape(info)
        escUser = conn.escape(userName)
        
        cur.execute("INSERT INTO TableOfPosts SET url = %s, title = %s, info = %s, username = %s ;" %(escUrl, escTitle, escInfo, escUser))

        conn.commit()
        cur.close()


def checkLoggedIn():
        loggedIn = False
        user = 'stranger'
        
        if 'username' in session:
                loggedIn = True
                user = session['username']
        return loggedIn, user

"""








                                                        ʕʘ̅͜ʘ̅ʔ
                                                        xhellox 










"""

@app.route('/login', methods=['GET','POST'])
def login():     
        if request.method == 'POST':
                
                theName = request.form['username']
                thePass = request.form['password']
                if checkUser(theName, thePass):

                        session['username'] = theName
                        session['password'] = thePass
                        return redirect(url_for('templateGreeting'))
                else:
                        return render_template('login_fail.html')
        return render_template('login.html')

       
        
    

@app.route('/')
@app.route('/home', methods=['GET','POST'])
def templateGreeting():
        loggedIn, user = checkLoggedIn()
                
        if request.method == 'POST':
                session['username'] = request.form['username']
                return redirect(url_for('/'))
        
        return render_template('index.html', loggedIn = loggedIn, user = user)

# render the page for adding new links
@app.route('/postlink')
def postALink():
    #name = request.args.get('name')
        loggedIn, user = checkLoggedIn()
        return render_template('postPage.html', loggedIn = loggedIn, user = user)

# rendering page with new links added
@app.route('/linkspace', methods = ['POST'])
def addLink(methods = None):
                                        
    link = request.form['url']
    siteName = request.form['siteName']
    info = request.form['info']
    loggedIn, username = checkLoggedIn()


    addLinkToDb(link, siteName, info, username)
    siteData = lookUpPosts()
                               
    return render_template('linkspace.html', siteData = siteData, loggedIn = loggedIn, user = username)

# display the links without adding new ones
@app.route('/linkspace')
@app.route('/linkspace', methods = ['GET'])
def displayLinks(methods = None):
        loggedIn, user = checkLoggedIn()

        siteData = lookUpPosts()
        return render_template('linkspace.html', siteData = siteData, loggedIn = loggedIn, user = user)



# render the comment thread for the post
@app.route('/comments/')
@app.route('/comments/<postID>/', methods = ['GET'])
def comments(postID = None):
        loggedIn, user = checkLoggedIn()
        
        if postID == None:
                return render_template('oops.html', loggedIn = loggedIn, user = user)
        else:
                currentPost = getPostDetails(postID)
        commentThread = getCommentsForPost(postID)
        
        
        return render_template('commentPage.html', currentPost = currentPost, commentThread = commentThread, user = user, loggedIn = loggedIn)


# add comments to the list of comments
@app.route('/comments/<postID>/', methods = ['POST'])
def postComment(postID):
        # get username and comment from form
        userComment = request.form['userComment']
        loggedIn, commenter = checkLoggedIn()

        # call function to append comments to comment list
        addCommentToDb(userComment, commenter, postID)

        # get necessary comment thread
        currentPost = getPostDetails(postID)
        commentThread = getCommentsForPost(postID)                        
        
        # render the template for that thread of comments   
        return render_template('commentPage.html', currentPost = currentPost, user = commenter, loggedIn = loggedIn, commentThread = commentThread)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('templateGreeting'))

#run that server yo
if __name__ == '__main__':
        app.secret_key = 'REMOVED'
        app.run(debug=True)
