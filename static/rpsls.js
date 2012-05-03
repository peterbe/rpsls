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
        currentIcon.animate({
            left: '65',
            top: '100',
            height: '250',
            width: '250'
          }, 500);
          currentIcon.parents('li').append('<p class="icon_name">' + currentIconClass + '</p>');
    });
})
