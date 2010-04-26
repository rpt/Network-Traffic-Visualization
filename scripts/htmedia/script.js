function click(id) {
    $("#ip_stats").attr("data", "htstats/ip-" + id + ".html");

    if ($("#ip_back").css("display") == "none") {
        $("#ip_back").fadeIn("fast", function() {
            $("#ip").fadeIn("fast");
       });
    }
}

function change(graph) {
	$("#svg").hide();
	$("#svg").attr("data", graph + ".svg");

	$("#ip_back").fadeIn("fast", function() {
		$("#svg").show();
		resize();
		redraw();
		$("#ip_back").fadeOut("fast");
	});
}

function resize() {
	window_aspect = $(window).width() / $(window).height();
	svg_aspect = $("#svg").width() / $("#svg").height();

	if ( window_aspect < svg_aspect || svg_aspect < 0.4 ) {
		tmp_height = 0.9 * $(window).width() / svg_aspect;
		$("#svg").height(tmp_height);
	}
	else {
		$("#svg").height(0.9 * $(window).height());
	}
}

function redraw() {

    width = $("#svg").width();
    height = $("#svg").height();

    if ( height <= $(window).height() ) {
        $("#svg").css("top", "50%");
        $("#svg").css("margin-top", -(height / 2));           
    }
    else {
        $("#svg").css("top", 0);
        $("#svg").css("margin-top", 0);
    }

    if ( width <= $(window).width() ) {
        $("#svg").css("left", "50%");
        $("#svg").css("margin-left", -(width / 2));
    }
    else {
        $("#svg").css("left", 0);
        $("#svg").css("margin-left", 0);
    }
}

$(document).ready(function() {

	resize();
	redraw();

    $("#zoom_in").click(function() {
        $("#svg").height(2 * $("#svg").height());
        redraw();
    });

    $("#zoom_out").click(function() {
        $("#svg").height($("#svg").height() / 2);
        redraw();
    });

    $("#ip_back").click(function() {
        $("#ip").fadeOut("fast", function() {
            $("#ip_back").fadeOut("fast");
        });
    });

    $(".trans").hover(function() {
        $(this).animate({opacity: "0.95"}, "fast");
    }, function() {
        $(this).animate({opacity: "0.5"}, "slow");
    });

    $("div#zoom img").hover(function() {
        $(this).animate({opacity: "0.95"}, 0);
    }, function() {
        $(this).animate({opacity: "0.5"}, 0);
    });
});
