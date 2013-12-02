$(document).ready(function() {
     audio = $("#theaudio")[0];
     renders = $('#renders');
     rendersMask = $('#rendersMask');
     capcal = $('#capcal');
     capcalTotal = $('#capcalTotal');
     renderTotal = $('#renderTotal');
     zoomFactor = "";
     waveform = $('#bigWave img');
     plButton = $("#control .plButton");
     timecode = $("#timecode");
     zooms = $(".zoom");
     // What point in seconds the left-hand side of the
     // image refers to.
     beginningOfView = 0;
	/* waveform.click(function(e) {
	 	var offset_l = $(this).offset().left - $(window).scrollLeft();
		var left = Math.round( (e.clientX - offset_l) );
	    mouPlay(left);
	});*/
     $(".zoom").click(function() {
         var level = $(this).data("length")
         zoom(level);
     });
     loaddata();

     $("#showRhythm").click(function(e) {
        drawwaveform();
     });
});

function spectrogram(context, view) {
    var waszero = false;
    context.moveTo(0, 10);
    context.lineTo(10, 10);
    context.moveTo(0,0);
    var skip = secondsPerView / 4;
    // Start is in samples
    var start = (beginningOfView / secondsPerView) * 900 * skip;
    // Number of pixels we draw
    var end = Math.min(900+start, view.length/skip);
    //console.debug("length " + view.length);
    //console.debug("skip " + skip);
    //console.debug("draw from " + start + " to " + end);
    for (var i = start; i < end; i++) {
        // Find our point
        var dataindex = i*skip;
        var data = view[dataindex];
        var xpos = i-start;
        // Invert on canvas
        var tmp = 255-data;
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
    }
    context.strokeStyle = "#eee";
    context.lineWidth = 2;
    context.stroke();
    context.beginPath();
    context.moveTo(0, 128);
    context.lineTo(900, 128);
    context.moveTo(0, 192);
    context.lineTo(900, 192);
    context.stroke();
}

function plothistogram() {
    var histogram = $("#histogramcanvas")[0];
    histogram.width = 200;
    histogram.height = 256;
    var context = histogram.getContext("2d");
    context.moveTo(180, 10);
    context.lineTo(200, 10);
    context.moveTo(200, 256);
    var max = 0;
    var data = histogramdata;
    for (var i = 0; i < data.length; i++) {
        if (data[i] > max) {
            max = data[i];
        }
    }
    var factor = 150 / max;
    for (var i = 0; i < data.length; i++) {
        v = data[i] * factor;
        context.lineTo(200-v, 256-i);
    }
    context.lineWidth = 2;
    context.stroke();
}

function plotpitch() {
    // In order to account for slow internet connections,
    // we always load one image ahead of what we need.
    // TODO: We need to know when the last image is.
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

function drawwaveform() {
    var wave = new Image();
    wave.src = waveformurl;
    var canvas = $("#rhythmcanvas")[0];
    canvas.width = 900;
    canvas.height = 256;
    var context = canvas.getContext("2d");
    wave.onload = function() {
        context.drawImage(wave, 0, 0);
        plotticks(context, rhythmdata);
        plottempo(context, aksharadata);
    }
}

function sortNumber(a,b) {
    return a - b;
}

function plotticks(context, data) {
    // TODO: it looked like for some of this data
    // we were sorting by asciibetical not numeric
    data.sort(sortNumber);
    from = data[0];
    to = data[data.length-1];
    $("#pulseFrom").html(formatseconds(from));
    $("#pulseTo").html(formatseconds(to));
    var show = $("#showRhythm").is(':checked');

    if ((secondsPerView == 8 || secondsPerView == 4) && show) {
        context.beginPath();
        console.debug("draw ticks");
        for (var i = 0; i < data.length; i++) {
            var val = data[i];
            var endVal = beginningOfView+secondsPerView;
            if (val > beginningOfView && val < endVal) {
                console.debug("got a tick at " + val);
                // We draw it.
                var position = val / endVal * 900;
                position = Math.floor(position) + 0.5;
                console.debug("drawing at " + position);
                context.moveTo(position, 0);
                context.lineTo(position, 255);
            }
        context.lineWidth = 1;
        context.stroke();
        }
        context.closePath();
    }
}

function plottempo(context, data) {
    var low = 1;
    var high = 0;
    for (var i = 0; i < data.length; i++) {
        var val = data[i][1];
        if (val > high) {
            high = val;
        }
        if (val < low) {
            low = val;
        }
    }
    $(".tempoup").html(high*1000 + " ms");
    $(".tempodown").html(low*1000 + " ms");
    high = high * 1.2;
    low = low * 0.8;
    var factor = 128 / (high - low);

    var secPerPixel = 900 / secondsPerView;
    var moved = false;
    for (var i = 0; i < data.length; i++) {
        var time = data[i][0];
        if (time >= beginningOfView) {
            // Data points are every 0.5 seconds
            // TODO: This doesn't draw the point at or near x=0
            var x = (time-beginningOfView) * secPerPixel;
            if (x > 900) {
                break;
            }
            var y = (data[i][1]-low) * factor;
            if (!moved) {
                context.moveTo(0, 256-y);
                moved = true;
            }
            context.lineTo(x, 256-y);
        }
    }
    context.strokeStyle = "#eee";
    context.lineWidth = 2;
    context.stroke();
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
    }});

    var ticksDone = false;
    var rhythmDone = false;

    $.ajax(rhythmurl, {dataType: "json", type: "GET", 
        success: function(data, textStatus, xhr) {
            rhythmdata = data;
            ticksDone = true;
            dodraw();
    }});

    $.ajax(aksharaurl, {dataType: "json", type: "GET", 
        success: function(data, textStatus, xhr) {
            aksharadata = data;
            rhythmDone = true;
            dodraw();
    }});

    function dodraw() {
        if (ticksDone && rhythmDone && pitchDone && histogramDone) {
            drawdata();
        }
    }
}

function drawdata() {
    drawwaveform();
    plotpitch();
    plothistogram();
    var start = beginningOfView;
    var skip = secondsPerView / 4;
    $(".timecode1").html(formatseconds(start));
    $(".timecode2").html(formatseconds(start+skip));
    $(".timecode3").html(formatseconds(start+skip*2));
    $(".timecode4").html(formatseconds(start+skip*3));
    $(".timecode5").html(formatseconds(start+skip*4));
}

function mouPlay(desti){
	posicio = renders.position();
	distclick = Math.abs(posicio.left)+desti;
	percentPunt = (distclick*100)/(waveform.width());
	nouPunt = (audio.duration*percentPunt)/100;
	console.log(nouPunt+" - "+audio.duration);
	audio.pause();
	audio.currentTime = Math.ceil(nouPunt);
	audio.play();
	audio.currentTime = Math.ceil(nouPunt);
}
function play() {
    audio.play();
    int = window.setInterval(updateProgress, 30);
}
function pause() {
    audio.pause();
    window.clearInterval(int);
}

function formatseconds(seconds) {
    progress_seconds = Math.ceil(seconds);
    progress_minutes = Math.floor(seconds/60);
    resto = (progress_seconds-(progress_minutes*60));
    if(resto<10){
		resto = "0"+resto;
    }
    if(progress_minutes<10){
		progress_minutes = "0"+progress_minutes;
    }
    timecodeHtml = ""+progress_minutes+":"+resto;
    console.debug("format seconds " + seconds);
    console.debug("format output  " + timecodeHtml);
    return timecodeHtml;
}

function updateProgress() {
    formattime = formatseconds(audio.currentTime);
    progress_percent = (audio.currentTime-beginningOfView) / secondsPerView * 100;
	ampleMask = rendersMask.width();
	ampleRenders = renders.width();
	ampleRenderTotal = renderTotal.width();
    nouLeft = ((ampleRenders*progress_percent)/100);
    nouLeft2 = ((ampleRenderTotal*progress_percent)/100);
    capcal.css('left',nouLeft);
    capcalTotal.css('left',nouLeft2);

    if (nouLeft2 > 900) {
        beginningOfView += secondsPerView;
        pnum = Math.floor(beginningOfView / secondsPerView + 1);
        waveformurl = waveformurl.replace(/part=[0-9]+/, "part="+pnum);
        specurl = specurl.replace(/part=[0-9]+/, "part="+pnum);
        drawdata();
    }
    timecode.html(formattime);
};

function zoom(level){
    secondsPerView = level;
    waveformurl = waveformurl.replace(/waveform[0-9]{1,2}/, "waveform"+level);
    specurl = specurl.replace(/spectrum[0-9]{1,2}/, "spectrum"+level);
    // When we go from a zoomed in to a zoomed out size,
    // we need to make sure that `beginningOfView` is on an
    // image boundary
    beginningOfView = Math.floor(beginningOfView / secondsPerView);
    pnum = Math.floor(beginningOfView / secondsPerView + 1);
    waveformurl = waveformurl.replace(/part=[0-9]+/, "part="+pnum);
    specurl = specurl.replace(/part=[0-9]+/, "part="+pnum);
    drawdata();
}

function playrecord(){
	if(plButton.hasClass("stop")){
		pause();
		plButton.removeClass("stop");
	}else{
		play();
		plButton.addClass("stop");
	}
}

