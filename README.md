
Default Folder X for Alfred
===========================


Show and search Default Folder X favourites and recent items in [Alfred][alfredapp].

**Note:** v0.3 and above are not compatible with Alfred 2!


Usage
-----

- `dfx [<query>]` — Show/search all DFX favourite/recent items.
    - `↩` or `⌘+<NUM>` — Open in default application.
    - `⌘+C` — Copy path to clipboard.
- `dfxf [<query>]` — Show/search only DFX favourite folders.
    - `↩` or `⌘+<NUM>` — Open in default application.
    - `⌘+C` — Copy path to clipboard.
- `dfxr [<query>]` — Show/search only DFX recent files/folders.
    - `↩` or `⌘+<NUM>` — Open in default application.
    - `⌘+C` — Copy path to clipboard.


Licencing, thanks
-----------------

This workflow is released under the [MIT licence][mit].

The main workflow icon is the property of the [magnificent folks at St. Clair Software][stclair].

It is based on the [Alfred-Workflow][aw] library, which is also released under the [MIT licence][mit].

This bloody useful workflow would not exist but for [nickwild][nickwild].


Changelog
---------

### 0.3.0 ###

- Remove update notification
- Use Alfred 3.2's re-run feature to update results when cached data are updated

### 0.2.0 ###

- Update folders in background
- Add auto-update info

### 0.1.0 ###

- First release


[mit]: ./src/LICENCE.txt
[aw]: http://www.deanishe.net/alfred-workflow/
[alfredapp]: https://www.alfredapp.com/
[stclair]: http://www.stclairsoft.com/
[nickwild]: http://www.alfredforum.com/topic/8695-default-folder-x/
