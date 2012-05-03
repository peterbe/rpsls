$(function() {
    $("#show_register").click(function(event) {
        event.preventDefault();
        $(".register").toggle();
    });
    
    $(".icon").click(function(event) {
        event.preventDefault();
        var currentIcon = $(this).find('img'),
        currentIconClass = $(this).find('img').attr('class');
        
        $(".play-icons img").not("." + currentIconClass).hide();
        currentIcon.addClass("chosen-weapon");
    });
});
