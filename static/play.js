var Status = (function() {
  var container = $('#status');
  function update(msg, color) {
    $('span', container).remove();
    $('<span>').addClass(color).text(msg).appendTo(container);
  }
  return {update: update};
})();

var Play = (function() {
  var _socket;
  var _ready = false;

  function init(socket) {
    _socket = socket;

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
    });

    $('form.play').submit(function() {
      var button = $('input[type="hidden"]', this).val();
      _socket.send_json({button: button});
      Status.update('Checking...');
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

    if (e.data.message) {
      $('<p>')
        .append($('<strong>').text(e.data.name + ': '))
          .append($('<time>').text(e.data.date))
            .append($('<span>').text(e.data.message))
              .appendTo($('#log'));
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

    }

  };
  sock.onclose = function() {
    console.log('closed');
    Status.update('Disconnected', 'red');
  };
  sock.onopen = function() {
    //log('opened');
    console.log('open');
    Status.update('Connected', 'green');
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
