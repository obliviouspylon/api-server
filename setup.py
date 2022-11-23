from git import Repo
from os import rmdir
# Set repos used
repos = {
    "gas-price-notification": {
        "URL" : "https://github.com/obliviouspylon/gas-price-notification"
    },
    "flights-in-radius":{
        "URL" : "https://github.com/obliviouspylon/flights-in-radius"
    }
}


# import repos
for name in repos:
    try:
        rmdir(name)
    except:
        pass

    try:
        Repo.clone_from(repos[name]["URL"], name)
    except:
        pass

