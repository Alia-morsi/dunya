var globalSpeed  = 500;

$(document).ready(function() {
    var cookieValue = $.cookie("cookieConsent");
    if (!cookieValue) {
        $("#cookie-bar").fadeIn(500);
    }
    $("#cookie-accept").click(function() {
        $.cookie("cookieConsent", "yes", { expires: 500, path: '/' });
        $("#cookie-bar").fadeOut(500);
    });
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
	var myTimer=false;
	$("#usermenuoptions").hover(function(){ clearTimeout(myTimer);});
    $('#usermenu').click(function() {
        $("#usermenuoptions").show({easing: "easeInOutQuad"});
        $(this).find('#usermenuoptions').addClass("open", globalSpeed, "easeInOutQuad");
    });
    $('#usermenu').mouseleave(function() {
		myTimer = setTimeout(function(){
			$("#usermenuoptions").hide({easing: "easeInOutQuad"});
			$(this).find('#usermenuoptions').removeClass("open", globalSpeed, "easeInOutQuad");
		}, 500)
    });

    $("#searchbox").autocomplete({
        source: "/carnatic/searchcomplete",
        minlength: 2,
        select: function(event, ui) {
            console.debug("select");
            console.debug(ui);
        }
    });
});
