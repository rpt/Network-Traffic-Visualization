function click(id) {
    $("#ip_stats").text(id);

    if ($("#ip_svg").width() != $("#ip").innerWidth()-20)
        $("#ip_svg").width($("#ip").innerWidth()-20);

    if ($("#ip_back").css("display") == "none") {
        $("#ip_back").fadeIn("fast", function() {
            $("#ip").fadeIn("fast");
            $("#ip_svg").attr("data", "ip-" + id + ".svg");
            $("#ip_svg_div").fadeIn("slow");
        });
    }
    else {
        $("#ip_svg_div").fadeOut("slow", function() {
            $("#ip_svg").attr("data", "ip-" + id + ".svg");
            $("#ip_svg_div").fadeIn("slow");
        });
    }
}

function change(graph) {
	$("#svg").hide();
	$("#svg").attr("data", graph + ".svg");

	$("#ip_back").fadeIn("fast", function() {
		$("#svg").show();
		$("#svg").height(0.9 * $(window).height());
		redraw();
		$("#ip_back").fadeOut("fast");
	});
}

function redraw() {

    width = $("#svg").width();
    height = $("#svg").height();

 //   alert(height);

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

    $("#svg").height(0.9 * $(window).height());
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
