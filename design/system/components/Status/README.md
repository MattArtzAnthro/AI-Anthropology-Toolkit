# Status

A word plus a mark that says where something stands; colour is never the only signal.

| tone | default word | mark | means |
|---|---|---|---|
| `needs` | Needs you | filled dot on a yellow pill | waiting on the researcher. The loudest thing on screen. |
| `started` | Started | hollow dot | touched but not recorded |
| `done` | Done | check | recorded |
| `refused` | Can't continue | cross | the server refused; pair with a Notice saying what to fix |
| `model` | Model draft | dashed dot | written by the model, nobody has decided it |

**Props** `tone` · `children`: replaces the default word ("Needs your ruling", "Ruled").

**Plain HTML** `<span class="aat-status aat-status--needs">Needs your ruling</span>`

**Don't** invent new tones or colours. Don't use `needs` for anything the researcher can't act on right now.
