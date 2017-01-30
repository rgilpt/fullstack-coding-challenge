/**
 * Created by rodrigo on 29-01-2017.
 */


$(document).ready(function(){

   
    // jQuery methods go here...
    $("#pt").click(function () {
        $.ajax({
            method: "GET",
            url: "/api/v1.0/translated_stories",
            data: {language_code: "pt"},
            success: function(result){
                $("#list-news").empty();
                stories = $("#list-news");
                $.each(result.stories, function (i) {
                    var li = $('<li/>')
                        .appendTo(stories);
                    var aaa =  $('<a/>')
                        .text(result.stories[i].title)
                        .appendTo(li);
                })
                $("#div1").html("");
             }});
        
    })
    $("#nl").click(function () {
        $.ajax({
            method: "GET",
            url: "/api/v1.0/translated_stories",
            data: {language_code: "nl"},
            success: function(result){
                $("#list-news").empty();
                stories = $("#list-news");
                $.each(result.stories, function (i) {
                    var li = $('<li/>')
                        .appendTo(stories);
                    var aaa =  $('<a/>')
                        .text(result.stories[i].title)
                        .appendTo(li);
                })
                $("#div1").html("");
             }});

    })
    $("#original").click(function () {
        $.ajax({
            method: "GET",
            url: "/api/v1.0/stories",
            success: function(result){
                $("#list-news").empty();
                stories = $("#list-news");
                $.each(result.stories, function (i) {
                    var li = $('<li/>')
                        .appendTo(stories);
                    var aaa =  $('<a/>')
                        .text(result.stories[i].title)
                        .appendTo(li);
                })
                $("#div1").html("");
             }});

    })

});