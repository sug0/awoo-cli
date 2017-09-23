# What this is

An awoo client for the terminal. Feel like a hacker browsing through quality shitposts.

# Requirements

`pip install -r requirements.txt`

# Usage

`$ python path/to/project/folder/` or `$ python path/to/project/folder/client.py`.

Make sure to copy `config.json` to `$HOME/.awoo.json` if not running from the project directory.

Also, populate the environment variables `$EDITOR` and `$PAGER`, respectively, with your favorite
text editor and text reader. Personally, I use `vim` and `less`, which work fine for this purpose.

# Tips

Install `rlwrap` for maximum profit. Run with something like:

    $ rlwrap -C awoo -f <(awoo-client/gen_awoo_autocomplete.py) python awoo-client/
