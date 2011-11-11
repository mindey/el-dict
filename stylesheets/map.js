$(document).ready(function() {
  var mapping={'orange1':'apelsinas1', 'orange2': 'oranžinė1'}

  $('#from').keyup(function(event) {
    var txt = $('#from').val()
    for (x in mapping)
    {
    txt = txt.replace(new RegExp(x, 'g'), mapping[x])
    }
    $('#to').text(txt);

  });

});
