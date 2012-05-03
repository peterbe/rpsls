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

  function init(socket) {
    _socket = socket;

    $('form.register').submit(function() {
      var nick = $('input[name="nick"]', this).val();
      if (!nick) {
        alert("Pick a name bastard!");
        return false;
      }
      _socket.send_json({register: nick});

      return false;
    });

    $('form.play').submit(function() {
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
  }
  return {init: init};

})();

SockJS.prototype.send_json = function(data) {
  this.send(JSON.stringify(data));
};

var initsock = function(callback) {
  sock = new SockJS('http://' + location.hostname + ':9999/play');

  sock.onmessage = function(e) {
    console.log('message', e.data);

    if (e.data.registered) {
      $('form.register').hide();
      $('.play-icons').show(500);
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
