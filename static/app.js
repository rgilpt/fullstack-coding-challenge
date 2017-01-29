/**
 * Created by rodrigo on 29-01-2017.
 */


$(document).ready(function(){

   
    // jQuery methods go here...
    $("#pt").click(function () {
        $.ajax({
            method: "GET",
            url: "/api/v1.0/stories",
            data: {language_code: "pt"},
            success: function(result){
                $("#list-news").empty();
                stories = $("#list-news");
                $.each(result.stories_translated, function (i) {
                    var li = $('<li/>')
                        .appendTo(stories);
                    var aaa =  $('<a/>')
                        .text(result.stories_translated[i].title_translated)
                        .appendTo(li);
                })
                $("#div1").html("");
             }});
        
    })

});