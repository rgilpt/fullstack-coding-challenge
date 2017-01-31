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

    function addKidComments(thisObj, comment) {
        if (comment != null) {
            var li = $('<li/>').appendTo(thisObj);
            var aaa =  $('<a/>')
                        .text(comment.text)
                        .appendTo(li);

            if(comment.hasOwnProperty('kids')){
                if(comment.kids.length > 0){
                    var ul = $('<ul/>').appendTo(thisObj);
                    $.each(comment.kids, function (i) {
                        addKidComments(ul, comment.kids[i])

                    });
                }
            }

            return li;
        }

    };
    $(".comment").click(function () {
        storyId = $(this).attr('data-index');
        $.ajax({
            method: "GET",
            url: "/api/v1.0/comments",
            data: {filter_story: storyId},
            success: function(result){
                $("#list-news").empty();
                stories = $("#list-news");
                $.each(result.comments, function (i) {
                    addKidComments(stories, result.comments[i]);
                    // li.appendTo(stories);
                    // var li = $('<li/>')
                    //     .appendTo(stories);
                    // var aaa =  $('<a/>')
                    //     .text(result.comments[i].text)
                    //     .appendTo(li);
                })
                // $("#div1").html("");
             }});

    })

});