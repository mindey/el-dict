$(document).ready(function() {

  $('#from').keyup(function(event) {
    var txt = $('#from').val()
    for (x in mapping)
    {
    txt = txt.replace(new RegExp(x, 'g'), mapping[x])
    }
    $('#to').text(txt);

  });

});
