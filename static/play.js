var Status = (function() {
  var container = $('#status');
  function update(msg, color) {
    $('span', container).remove();
    $('<span>').addClass(color).text(msg).appendTo(container);
  }

  function update_score(wins, draws, losses) {
    var c = $('#score-status');
    $('.wins span', c).text(wins);
    $('.draws span', c).text(draws);
    $('.losses span', c).text(losses);
    $('#score-status:hidden').show();
  }

  return {
     update: update,
      update_score: update_score
  };
})();

var Play = (function() {
  var _socket;
  var _ready = false;

  function reset_animation() {
    $("form.restart").hide();
    $(".play-icons img").not(".chosen-weapon").show();
    $(".play-icons img").removeClass('chosen-weapon');
  }

  function init(socket) {
    _socket = socket;

    $('form.restart').submit(function() {
      reset_animation();
      Status.update('Ready to play', 'green');
      _ready = true;
      return false;
    });

    $('form.chat').submit(function() {
      var name = $.trim($('input[name="name"]').val());
      var message = $.trim($('input[name="message"]').val());
      if (!name.length) {
        alert("No name :(");
      } else if (!message.length) {
        $('input[name="message"]').focus();
      } else {
        _socket.send_json({name: name, message: message});
        $('input[name="message"]').val('');
        $('input[name="message"]').focus();
      }
      return false;
    });

    $('li.icon').on('click', function() {
      if (!_ready) return;
      var f = $('form.play');
      $('input[type="hidden"]', f).remove();
      $('<input type="hidden" name="chosen">')
        .val($(this).data('button'))
        .appendTo(f);
      Status.update('Button chosen', 'orange');
      f.show();
      setTimeout(function() {
        if ($('form.play:visible').size()) {
          $('form.play').submit().hide();
        }
      }, 2 * 1000);
    });

    $('form.play').submit(function() {
      var button = $('input[type="hidden"]', this).val();
      _socket.send_json({button: button});
      Status.update('Checking...', 'orange');
      $(this).hide();
      return false;
    });
  }

  function has_logged_in(email) {
    _socket.send_json({register: email});
  }

  function set_ready(toggle) {
    _ready = toggle;
    Status.update('Ready to play', 'green');
  }

  return {
     init: init,
      has_logged_in: has_logged_in,
      set_ready: set_ready
  };

})();

SockJS.prototype.send_json = function(data) {
  this.send(JSON.stringify(data));
};

var initsock = function(callback) {
  sock = new SockJS('http://' + location.hostname + ':9999/play');

  sock.onmessage = function(e) {
    console.log('message', e.data);

    if (e.data.registered) {
      $('.auth').hide();
      $('.play-icons, .chat').fadeIn(500);
      Status.update('Registered', 'black');
      $('input[name="name"]').val(e.data.registered);
    }

    if (e.data.status) {
      Status.update(e.data.status, e.data.color || 'black');
    }

    if (e.data.update_score) {
      Status.update_score(e.data.update_score.wins,
                          e.data.update_score.draws,
                          e.data.update_score.losses);

    }

    if (e.data.message) {
      $('<p>')
        .append($('<strong>').text(e.data.name + ': '))
          .append($('<time>').text(e.data.date))
            .append($('<span>').text(e.data.message))
              .appendTo($('#log'));
        $('#log').scrollTop($('#log').scrollTop() + 1000);
    }

    if (e.data.ready) {
      Play.set_ready(true);
    }

    if (e.data.won) {
      if (e.data.won == 1) {
        Status.update('You won!!!', 'green');
      } else {
        Status.update('You lost :(', 'red');
      }
    } else if (e.data.draw) {
      Status.update("It's a Draw!", 'orange');
    }

    if (e.data.won || e.data.draw) {
      setTimeout(function() {
        $('form.restart').fadeIn(500);
        setTimeout(function() {
          $('form.restart:visible').submit();
        }, 3 * 1000);
      }, 1 * 1000);
    }

  };
  sock.onclose = function() {
    console.log('closed');
    Status.update('Disconnected', 'red');
  };
  sock.onopen = function() {
    //log('opened');
    console.log('open');
    Status.update('Connected but not logged in', 'green');
    //sock.send('test');
    if (sock.readyState !== SockJS.OPEN) {
      throw "Connection NOT open";
    }
    callback(sock);
  };
};


$(function() {
  console.log('let the madness begin!');
  initsock(function(socket) {
    Play.init(socket);
  });
});
