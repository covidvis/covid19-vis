WebFontConfig = {
    google: {
        families: ['Khula:300'],
    },
    /* Called when all the specified web-font provider modules (google, typekit, and/or custom) have reported that they have started loading fonts. */
    loading: function() {
        // do something
    },
    /* Called when each requested web font has started loading. The fontFamily parameter is the name of the font family, and fontDescription represents the style and weight of the font. */
    fontloading: function(fontFamily, fontDescription) {
        // do something
    },
    /* Called when each requested web font has finished loading. The fontFamily parameter is the name of the font family, and fontDescription represents the style and weight of the font. */
    fontactive: function(fontFamily, fontDescription) {
        // do something
    },
    /* Called if a requested web font failed to load. The fontFamily parameter is the name of the font family, and fontDescription represents the style and weight of the font. */
    fontinactive: function(fontFamily, fontDescription) {
        // do something
    },
    /* Called when all of the web fonts have either finished loading or failed to load, as long as at least one loaded successfully. */
    active: startVegaEmbedding,
    /* Called if the browser does not support web fonts or if none of the fonts could be loaded. */
    inactive: function() {
        // do something
    }
};

/* async! */
(function() {
    var wf = document.createElement('script');
    wf.src = ('https:' == document.location.protocol ? 'https' : 'http') + '://ajax.googleapis.com/ajax/libs/webfont/1/webfont.js';
    wf.type = 'text/javascript';
    wf.async = 'true';
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(wf, s);
})();
