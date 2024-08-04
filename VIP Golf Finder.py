import time, requests, bs4, datetime, os, sys, getpass, threading

UPDATE_NAME = "Version 1.2.1"
DEBUG = False

members = []

class Member:
    def __init__(self, dataList):
        self.date = dataList[0]
        self.time = dataList[1]
        self.id = int(dataList[2])
        self.name = dataList[3] + " " + dataList[4]
        self.booked = dataList[5]

    def printUser(self):
        print(f"{self.date:10s} | {self.time:5s} | {self.id:5d} | {self.name:35s} | {self.booked:2s}")

def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')

def playIntro(animation=True):
    clearScreen()
    logo = """__     _____ ____     ____       _  __   _____ _           _           
\ \   / /_ _|  _ \   / ___| ___ | |/ _| |  ___(_)_ __   __| | ___ _ __ 
 \ \ / / | || |_) | | |  _ / _ \| | |_  | |_  | | '_ \ / _` |/ _ \ '__|
  \ V /  | ||  __/  | |_| | (_) | |  _| |  _| | | | | | (_| |  __/ |   
   \_/  |___|_|      \____|\___/|_|_|   |_|   |_|_| |_|\__,_|\___|_|   
"""
    creditText = "By: Adam Olsen"
    for line in logo.splitlines("\n"):
        if animation:
            for n in line:
                print(n,end="")
                sys.stdout.flush()
                time.sleep(0.008)
            time.sleep(0.1)
        else:
            print(line,end="")
    print(" " * (len(logo.splitlines("\n")[0]) - len(UPDATE_NAME)) + UPDATE_NAME)
    print(" " * (len(logo.splitlines("\n")[0]) - len(creditText)) + creditText)
    if animation: time.sleep(2)

def loginVIPDay(username, password, theUrl):
    # Start HTML Parser
    session = requests.Session()
    response = session.get(theUrl)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': '_csrfToken'}).get('value')

    # Create payload
    payload = {
        'username': username,
        'password': password,
        '_csrfToken': csrf_token  # Include CSRF token in payload
    }
    
    # Post login form with CSRF token
    post = session.post(url="https://members.vipgolf.ca/users/login", data=payload)
    if DEBUG: print("URL: " + theUrl)
    
    # Check if login was successful
    if post.status_code == 200:
        r = session.get(theUrl)
        if "Your username or password doesn" in post.text:
            print("Username / Password does not exist. Please re-open program to retry.\nClosing automatically in 3 seconds...")
            time.sleep(3)
            exit(1)
        return r.text
    else:
        print("Login failed")

def getMembers(username,password,url):
    # Get Website info
    websiteInfo = loginVIPDay(username,password,url).split()
    lines = []
    
    # Remove all extra space
    for line in websiteInfo:
        lines.append(line.rstrip())
    
    # Reset the number of members on a given day
    n = 0
    members.clear()
    
    # Check for a table row. If said row exists, check if it is of style no-wrap (signifying a name row)
    while n < (len(lines)) - 1:
        if lines[n] == "<tr>":
            userInfo = []
            for m in range(20):
                if DEBUG: print(m,lines[n+m])
                if 'text-nowrap">' in lines[n+m]:
                    userInfo.append(str(lines[n+m].removeprefix('text-nowrap">')).removesuffix("</td>"))
                # For some reason if the users name contains an ' then it adds another row so that is cool. So have to hardcode for the extra line row 19 :)
                elif m == 19 and lines[n+m] in list(str(x) for x in range(10)):
                    userInfo.append(str(lines[n+m]))
                elif m == 19:
                    userInfo.append(str(lines[n+m+1]))
            if DEBUG: print("-" * 20)
            if len(userInfo) == 6:
                members.append(Member(userInfo))
        n += 1

    if DEBUG:
        print("-" * 25)
        for member in members:
            member.printUser()

strings = []

def getCountOfMembers(date):
    # Count the number of players on that date
    count = 0
    for member in members:
        try:
            count += int(member.booked)
        # Have to check for exceptions, as if the user has the char ' in their name, VIP adds an extra line for some reason :)
        except Exception as e:
            count += 1
            
    # Create the string that will be printed and append it to the list of strings generated.
    countString = f"({count:2d} / 24) | [" + ("X" * count) + ("-" * (24 - count)) + "]"
    strings.append((date,date.strftime("%a, %b %d") + " | " + countString))

def getDates():
    # Checks the current day, and then the next 7 days in the future
    dates = []
    for n in range(8):
        dates.append((datetime.date.today() + datetime.timedelta(days=n)))
    return dates

def processMembers(date, username, password):
    strDate = date.strftime("%Y-%m-%d")
    getMembers(username,password,"https://members.vipgolf.ca/users/courseadmin/74/" + strDate + "%20to%20" + strDate)
    getCountOfMembers(date)

def main():
    # Play the intro
    playIntro(True)
    
    # Get info about the date(s)
    dates = getDates()
    
    # Get User's Username and Password
    username = input("What is your username: ")
    password = getpass.getpass("What is your password: ", stream=None)
    
    while True:
        # Play intro without animation
        playIntro(False)
        # Get the current time
        lastTime = datetime.datetime.today()
        
        # Clear Globals
        strings.clear()
        members.clear()

        # Create a thread for each date
        threads = []
        for date in dates:
            thread = threading.Thread(target=processMembers, args=(date,username,password))
            threads.append(thread)
            thread.start()
        
        # Wait for each thread to complete
        for thread in threads:
            thread.join()
        
        # Sort the strings by date, as some might complete before others
        newStrings = sorted(strings, key=lambda x: x[0])
        for string in newStrings:
            print(string[1])
        
        # Print the timestamp at which the threads complete 
        print("-" * 75, f"\nLast Updated: " + lastTime.strftime("%a, %b %d @ %I:%M:%S%p"))
        input("Press [Enter] to refresh the VIP List\n\n")
            
if __name__ == "__main__":
    main()