# Bot-à-Plot

![Main](https://github.com/armyofevilrobots/bot-a-plot/actions/workflows/python-app.yml/badge.svg?branch=main)

![alt text](doc/img/botaplot_screenshot.png "Bot-à-Plot")

Bot-a-Plot is a plotter runner and (eventually) generative art environment
for python developers. It currently supports g-code based post processing of
SVG files into G-code, and also operates a plotter either
locally over USB/Serial, or remotely over Telnet.
Jobs can be paused/cancelled, and pen/plotter position can
be managed.

Coming soon is:

 * Multi-layer support and post-processing, including translation/rotation
 * Multiple pens and toolchangers
 * Python SVG generation and post-processing with arbitrary python files
 * Unlimited Undo levels
 * Writing SVGs
 * Advanced path optimization and draw ordering, path merging, pen-lift
   limiting and joining.
