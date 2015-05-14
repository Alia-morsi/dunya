allpeaks = {"11a44af7-e29a-4c50-aa38-6139d37ca306":
    {"99": "2", "133": "5", "169": "1'", "112": "3", "148": "6", "86": "1", "183": "2'"},
    "067b8f25-888a-4a08-a495-cbc402846b10": {"161": "7", "196": "3'", "133":
        "5", "97": "2", "170": "1'", "110": "3", "147": "6", "86": "1", "118":
            "4", "62": "6.", "182": "2'"},
    "83d2fc7f-e1c1-4359-b417-ed9e519ecbb7": {"160": "7", "98": "2", "133": "5",
        "170": "1'", "111": "3", "146": "6", "181": "2'", "86": "1"},
    "415d9fcc-bad8-45db-adec-01ffd04b9cec": {"96": "2", "132": "5", "5":
        "1.", "76": "7.", "45": "5.", "14": "2.", "110": "3", "119": "4",
        "28": "3.", "61": "6.", "85": "1"},
    "0b5dd02b-d93e-4b44-81a3-d789f29ddb7d": {"97": "2", "132": "5", "85":
        "1", "110": "3", "63": "6."},
    "87b5c1b2-e718-4ae7-8662-dc4ae3efd3b1": {"96": "2", "131": "5",
            "84": "1", "62": "6.", "110": "3"}}

banshipalette = ["rgba(149,32,11,0.5)", "rgba(187,57,34, 0.5)", "rgba(217,90,67, 0.7)", "rgba(247,130,109, 0.7)", "rgba(255,170,154, 0.7)"];
var banshicolours = {}

$(document).ready(function() {
     hasfinished = false;
     pagesound = ""
     audio = $("#theaudio")[0];
     renders = $('#renders');
     rendersMask = $('#rendersMask');
     capcal = $('#capcal');
     capcalTotal = $('#capcalTotal');
     renderTotal = $('#renderTotal');
     zoomFactor = "";
     waveform = $('#renderTotal canvas');
     plButton = $("#control .plButton");
     timecode = $("#timecode");
     zooms = $(".zoom");
     // What point in seconds the left-hand side of the
     // image refers to.
     beginningOfView = 0;
     // The 900 pitch values currently on screen
     pitchvals = new Array(900);
	 waveform.click(function(e) {
	 	var offset_l = $(this).offset().left - $(window).scrollLeft();
		var left = Math.round( (e.clientX - offset_l) );
	    mouPlay(left);
	 });
     waveform.mouseenter(function(e) {
         if (pagesound && pagesound.duration) {
             waveform.css("cursor", "pointer");
         } else {
             waveform.css("cursor", "wait");
         }
     });
     waveform.mousemove(function(e) {
         if (pagesound && pagesound.duration) {
             var offset_l = $(this).offset().left - $(window).scrollLeft();
             var left = Math.round( (e.clientX - offset_l) );
             var miniviewWidth = renderTotal.width();
             var miniviewPercent = left / miniviewWidth;
             var timeseconds = Math.floor(recordinglengthseconds * miniviewPercent);

             $("#timepoint").html(formatseconds(timeseconds));
             $("#timepoint").show();
             var offset = $("#renderTotal").offset();
             $("#timepoint").css({
                 "top" : e.pageY - offset.top,
                 "left" : e.pageX - offset.left + 15
             });
        }
     });
     waveform.mouseleave(function() {
        $("#timepoint").hide();
     });
     $(".zoom").click(function(e) {
         e.preventDefault();
         // Remove selected
         $(".zoom").removeClass("selected");
         // Find all zooms with all our classes (e.g. 'zoom zoom<n>')
         // and apply 'selected'
         var zclasses = $(this).attr("class");
         $("[class='"+zclasses+"']").addClass("selected");
         var level = $(this).data("length");
         zoom(level);
     });
     loaddata();

     soundManager.onready(function() {
         pagesound = soundManager.createSound({
               url: audiourl,
         });
     });

     $(document).keypress(function(e) {
         // The Space key is play/pause unless in the searchbox
         if ((e.keyCode == 0 || e.keyCode == 32) && !$(e.target).is("#searchbox")) {
             e.preventDefault();
             playrecord();
         }
     });
});

function plottonic(context) {
    context.beginPath();
    // tonic (first degree)
    context.moveTo(0, 170.5);
    context.lineTo(900, 170.5);
    if (drawoctave) {
        // sa+1, dotted
        context.moveTo(0, 128.5);
        for (var i = 0; i < 900; i+=10) {
            context.moveTo(i, 85.5);
            context.lineTo(i+5, 85.5);
        }
    }
    context.strokeStyle = "#eee";
    context.lineWidth = 1;
    context.stroke();
    context.closePath();
}

function spectrogram(context, view) {
    plottonic(context);
    plotticks(context);
    var waszero = false;
    context.moveTo(0, 10);
    context.lineTo(10, 10);
    context.moveTo(0,0);
    var skip = secondsPerView / 4;
    // Start is in samples
    var start = (beginningOfView / secondsPerView) * 900 * skip;
    // Number of pixels we draw
    var end = Math.min(900+start, start+(view.length-start)/skip);
    var remaining = view.length-start;
    //console.debug("length " + view.length);
    //console.debug(remaining + " samples remaining");
    //console.debug("with skip, " + (remaining/skip) + " rem");
    //console.debug("skip " + skip);
    //console.debug("draw from " + start + " to " + end);
    context.beginPath();
    for (var i = start; i < end; i++) {
        // Find our point
        var xpos = i-start;
        var dataindex = start + xpos*skip;
        var data = view[dataindex];
        // Invert on canvas
        var tmp = 255-data;
        //console.debug(" at ("+xpos+","+tmp+") data " + dataindex);
        // We choose 0 if the pitch is unknown, or 255 if it's
        // higher than the 3 octaves above tonic. If so, we don't
        // want to draw something, just skip until the next value
        if (tmp == 0 || tmp == 255) {
            waszero = true;
            context.moveTo(xpos, tmp);
        } else {
            if (waszero) {
                waszero = false;
                context.moveTo(xpos, tmp);
            } else {
                context.lineTo(xpos, tmp);
            }
        }
        // Set the pitchvals so we can draw the histogram
        pitchvals[xpos] = tmp;
    }

    //context.strokeStyle = "#e71d25";
    context.strokeStyle = "#eee";
    context.lineWidth = 2;
    context.stroke();
    context.closePath();
}

function plothistogram(pitch) {
    pitch = pitch || 0;
    var histogram = $("#histogramcanvas")[0];
    histogram.width = 200;
    histogram.height = 256;
    var context = histogram.getContext("2d");
    //context.moveTo(180, 10);
    //context.lineTo(200, 10);
    //context.moveTo(200, 256);
    var max = 0;
    var data = histogramdata;
    for (var i = 0; i < data.length; i++) {
        if (data[i] > max) {
            max = data[i];
        }
    }
    var factor = 150 / max;
    context.beginPath();
    var numbers = allpeaks[mbid];
    for (var i = 0; i < data.length; i++) {
        var v = Math.round(data[i] * factor)+0.5;
        if (numbers[i]) {
            context.fillStyle = "#000";
            context.font = "12px Arial";
            context.fillText(numbers[i], v+7, 256-i+3);
        }
        context.lineTo(v, 256-i);
    }
    context.lineWidth = 2;
    context.strokeStyle = "#e71d25";
    context.stroke();
    context.closePath();

    // Pitch
    if (pitch > 0 && pitch < 255) {
        pitch = Math.floor(pitch) + 0.5;
        context.beginPath();
        context.moveTo(0, pitch);
        context.lineTo(200, pitch);
        context.lineWidth = 1;
        context.strokeStyle = "#000";
        context.stroke();
        context.closePath();
    }
}

function plotpitch() {
    // In order to account for slow internet connections,
    // we always load one image ahead of what we need.
    // TODO: We need to know when the final image is.
    var spec = new Image();
    spec.src = specurl;
    var view = new Uint8Array(pitchdata);
    var canvas = $("#pitchcanvas")[0];
    canvas.width = 900;
    canvas.height = 256;
    var context = canvas.getContext("2d");
    spec.onload = function() {
        context.drawImage(spec, 0, 0);
        spectrogram(context, view);
    }
}

function sortNumber(a,b) {
    return a - b;
}

function plotticks(context) {
    // Plot the beginning and ending of banshi and lougu
    // If it's started, show the name of it at the top

    var loopData = function(data) {
        context.beginPath();
        for (var i = 0; i < data.length; i++) {
            var d = data[i];
            var name = d[0];
            var start = d[1];
            var end = d[2];
            var viewstart = beginningOfView;
            var viewend = viewstart + secondsPerView;
            if (start > viewstart && start < viewend) {
                //console.debug("data starts here at " + start);
                // Starting line + name in this view
                var position = (start-beginningOfView) / secondsPerView * 900;
                position = Math.floor(position) + 0.5;

                context.moveTo(position, 0);
                context.lineTo(position, 255);
                context.lineWidth = 1;
                context.strokeStyle = "#eee";
                context.stroke();

                //context.fillStyle = "#eee";
                //context.font = "bold 25px Arial";
                //context.fillText(name, position + 20, 40);

            } else if (start < viewstart && end > viewstart) {
                // Name, at the beginning of this view
                //context.fillStyle = "#eee";
                //context.font = "bold 25px Arial";
                //context.fillText(name, 20, 40);
            } else if (end > viewstart && end < viewend) {
                // End line in this view
                var position = (start-beginningOfView) / secondsPerView * 900;
                position = Math.floor(position) + 0.5;

                context.moveTo(position, 0);
                context.lineTo(position, 255);
                context.moveTo(position, 0);
                for (var i = 0; i < 255; i+=10) {
                    context.moveTo(position, 0);
                    context.lineTo(position, i+0.5);
                }
                context.lineWidth = 1;
                context.strokeStyle = "#eee";
                context.stroke();
            }
        }
        context.closePath();
    };

    loopData(banshidata);
    loopData(luogudata);
}


function loaddata() {
    // We do pitch track with manual httprequest, because
    // we want typedarray access

    histogramDone = false;
    pitchDone = false;
    var oReq = new XMLHttpRequest();
    oReq.open("GET", pitchtrackurl, true);
    oReq.responseType = "arraybuffer";
    oReq.onload = function(oEvent) {
        if (oReq.status == 200) {
            pitchdata = oReq.response;
            pitchDone = true;
            dodraw();
        }
    };
    oReq.send();
    $.ajax(histogramurl, {dataType: "json", type: "GET",
        success: function(data, textStatus, xhr) {
            histogramdata = data;
            histogramDone = true;
            dodraw();
    }, error: function(xhr, textStatus, errorThrown) {
       console.debug("xhr error " + textStatus);
       console.debug(errorThrown);
    }});

    luoguDone = false;
    $.ajax(luoguurl, {dataType: "json", type: "GET",
        success: function(data, textStatus, xhr) {
            luogudata = data;
            luoguDone = true;
            dodraw();
    }, error: function(xhr, status, error) {
        //console.debug("no luogu, skipping");
          luogudata = [];
          luoguDone = true;
          dodraw();
    }});

    banshiDone = false;
    $.ajax(banshiurl, {dataType: "json", type: "GET",
        success: function(data, textStatus, xhr) {
            banshidata = data;
            banshiDone = true;
            dodraw();
    }});

    lyricsDone = false;
    $.ajax(lyricsurl, {dataType: "json", type: "GET",
        success: function(data, textStatus, xhr) {
            lyricsdata = data;
            lyricsDone = true;
            dodraw();
    }});

    function dodraw() {
        if (pitchDone && histogramDone && banshiDone &&
                luoguDone && lyricsDone) {
            drawdata();
        }
    }
}

function plotsmall() {
    var pxpersec = 900.0/recordinglengthseconds;
    var smallFill = function(data, colour) {
        context.fillStyle = colour;
        for (var i = 0; i < data.length; i++) {
            var d = data[i];
            var txt = d[0];
            var s = d[1];
            var e = d[2];
            if($.type(colour) === "string") {
                context.globalAlpha = 0.5;
                context.fillStyle = colour;
            } else {
                var col = colour[txt];
                context.globalAlpha = 1;
                context.fillStyle = col;
            }
            var spos = Math.round(s * pxpersec)+0.5;
            var epos = Math.round(e * pxpersec)+0.5;
            context.fillRect(spos, 0, epos-spos, 64);
        }
    };
    var small = new Image();
    small.src = smallurl;
    var canvas = $("#smallcanvas")[0];
    canvas.width = 900;
    canvas.height = 64;
    var context = canvas.getContext("2d");
    small.onload = function() {
        context.drawImage(small, 0, 0, 900, 64, 0, 0, 900, 64);
        smallFill(banshidata, banshicolours);
        smallFill(luogudata, "#0f0");
    }
}

function drawtext() {
    var viewStart = beginningOfView;
    var viewEnd = beginningOfView + secondsPerView;

    function singletext(theid, theclass, data, colours) {
        $("#"+theid + " ."+theclass).remove();
        for (var i = 0; i < data.length; i++) {
            var d = data[i];
            var word = d[0];
            var s = d[1];
            var e = d[2];
            var col = colours[word];
            if (s >= viewStart && s < viewEnd) {
                var position = (s-beginningOfView) / secondsPerView * 900;
                if (e <= viewEnd) {
                    var width = (e-beginningOfView) / secondsPerView * 900;
                } else {
                    // Until the end: 900 pixels wide, minus where we start from
                    var width = 900 - position;
                }

                $("<div>", {
                    text: word,
                    class: theclass,
                }).css("left", position+"px").css("background-color", col).css("width", width).appendTo("#"+theid)
            } else if (s < viewStart && e > viewStart) {
                var position = (s-beginningOfView) / secondsPerView * 900;
                if (e <= viewEnd) {
                    var width = (e-beginningOfView) / secondsPerView * 900;
                } else {
                    // Until the end: 900 pixels wide, minus where we start from
                    var width = 900 - position;
                }
                $("<div>", {
                    text: word,
                    class: theclass,
                }).css("left", "0px").css("background-color", col).css("width", width).appendTo("#"+theid)
            }
        }
    }

    singletext("lyrics", "lyric", lyricsdata, {});
    singletext("banshis", "banshi", banshidata, banshicolours);
    singletext("percussions", "percussion", luogudata, {});
}

function drawdata() {
    // Read the banshi data and make a map of banshiname -> unique colour:

    var paletteind = 0;
    for (var i = 0; i < banshidata.length; i++) {
        var t = banshidata[i][0];
        if (!banshicolours[t]) {
            banshicolours[t] = banshipalette[paletteind];
            paletteind += 1;
        }
    }
    //console.debug(banshicolours);

    plotpitch();
    plothistogram();
    plotsmall();
    drawtext();
    var start = beginningOfView;
    var skip = secondsPerView / 4;
    $(".timecode1").html(formatseconds(start));
    $(".timecode2").html(formatseconds(start+skip));
    $(".timecode3").html(formatseconds(start+skip*2));
    $(".timecode4").html(formatseconds(start+skip*3));
    $(".timecode5").html(formatseconds(start+skip*4));

    // The highlighted miniview
    var beginPercentage = (beginningOfView/recordinglengthseconds);
    var endPercentage = (beginningOfView+secondsPerView) / recordinglengthseconds;

    var beginPx = renderTotal.width() * beginPercentage;
    var endPx = renderTotal.width() * endPercentage;
    var mini = $('#miniviewHighlight');
    mini.css('left', beginPx);
    mini.css('width', endPx-beginPx);
}

function mouPlay(desti){
	percent = desti/waveform.width();
    clickseconds = recordinglengthseconds * percent

    posms = clickseconds * 1000;
    part = Math.ceil(clickseconds / secondsPerView);
    // Update the internal position counter (counts from 0, part counts from 1)
    beginningOfView = (part - 1) * secondsPerView;

    if (pagesound && pagesound.duration) {
        // We can only set a position if it's fully loaded
        var wasplaying = !pagesound.paused;
        if (wasplaying) {
            pagesound.pause();
        }
        pagesound.setPosition(posms);
        replacepart(part);
        updateProgress();
        if (wasplaying) {
            pagesound.resume();
        }
    }
}

function play() {
    if (hasfinished) {
        hasfinished = false;
        replacepart(1);
        beginningOfView = 0;
        drawdata();
    }
    pagesound.play({onfinish: function() {
        window.clearInterval(int);
        plButton.removeClass("stop");
        hasfinished = true;
    }});
    int = window.setInterval(updateProgress, 30);
}
function pause() {
    pagesound.pause();
    window.clearInterval(int);
}

function formatseconds(seconds) {
    progress_seconds = Math.ceil(seconds);
    progress_minutes = Math.floor(seconds/60);
    resto = (progress_seconds-(progress_minutes*60));
    // never show :60 in seconds part
    if (resto >= 60) {
        resto = 0;
        progress_minutes += 1;
    }
    if(resto<10){
		resto = "0"+resto;
    }
    if(progress_minutes<10){
		progress_minutes = "0"+progress_minutes;
    }
    timecodeHtml = ""+progress_minutes+":"+resto;
    return timecodeHtml;
}

function replacepart(pnum) {
    specurl = specurl.replace(/part=[0-9]+/, "part="+pnum);
    drawdata();
}

function updateProgress() {
    var currentTime = pagesound.position / 1000;
    // formatseconds appears to run 1 second ahead of time,
    // so correct for it here
    formattime = formatseconds(currentTime-1);
    progress_percent = (currentTime-beginningOfView) / secondsPerView * 100;
    total_progress_frac = (currentTime/recordinglengthseconds);
	ampleMask = rendersMask.width();
	ampleRenders = renders.width();
	ampleRenderTotal = renderTotal.width();
    leftLargeView = ((ampleRenders*progress_percent)/100);
    leftSmallView = ampleRenderTotal*total_progress_frac;
    capcal.css('left', leftLargeView-5);
    capcalTotal.css('left', leftSmallView-6);

    if (leftLargeView > 900) {
        beginningOfView = Math.floor(currentTime / secondsPerView) * secondsPerView;
        pnum = Math.floor(beginningOfView / secondsPerView + 1);
        replacepart(pnum)
    }
    timecode.html(formattime + "<span>"+recordinglengthfmt+"</span>");

    // Current pitch
    var pitchindex = Math.floor(leftLargeView);
    var p = pitchvals[pitchindex];
    plothistogram(p);
};

function zoom(level){
    secondsPerView = level;
    specurl = specurl.replace(/spectrum[0-9]{1,2}/, "spectrum"+level);
    // When we go from a zoomed in to a zoomed out size,
    // we need to make sure that `beginningOfView` is on an
    // image boundary
    beginningOfView = Math.floor(beginningOfView / secondsPerView);
    pnum = Math.floor(beginningOfView / secondsPerView + 1);
    specurl = specurl.replace(/part=[0-9]+/, "part="+pnum);
    drawdata();

}


