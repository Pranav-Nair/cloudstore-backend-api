import validators
from database import User
def isvalidpasswd(passwd):
    state=True
    if len(passwd) <8:
        state=False
    if " " in passwd:
        state=False
    return state

def idvalidemail(email):
    stat = True
    if not validators.email(email):
        stat=False
    if User.objects(email=email):
        stat=False
    return stat

def isvalidpath(path):
    stat =True
    if not path:
        return False
    notval = ["/","\\"," "]
    if len(path) == 1:
        if path in notval:
            stat=False
    else:
        if path[0] in notval or path[len(path)-1] in notval:
            stat = False
    return stat
