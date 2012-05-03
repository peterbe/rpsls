var Chat = (function() {
  var _socket;

  function init(socket) {
    _socket = socket;
    $('form').submit(function() {
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
    $('<p>')
      .text(e.data.date)
        .css('float', 'right')
          .appendTo($('#log'));
    $('<p>')
      .append($('<strong>').text(e.data.name + ': '))
        .append($('<span>').text(e.data.message))
          .appendTo($('#log'));
  };
  sock.onclose = function() {
    console.log('closed');
  };
  sock.onopen = function() {
    //log('opened');
    console.log('open');
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
    Chat.init(socket);
  });
});
