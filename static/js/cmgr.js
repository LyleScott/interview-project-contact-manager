  $(function() {
    var firstname = $("#firstname"),
        lastname = $("#lastname"),
        zipcode = $("#zipcode"),
        allFields = $([])
          .add(firstname)
          .add(lastname)
          .add(zipcode),
        tips = $(".validateTips");

    function updateTips( t ) {
      tips
        .text(t)
        .addClass("ui-state-highlight");
      setTimeout(function() {
        tips.removeClass("ui-state-highlight", 1500);
      }, 500 );
    }

    function checkLength(o, n, min, max) {
      if (o.val().length > max || o.val().length < min) {
        o.addClass("ui-state-error");
        updateTips("Length of " + n + " must be between " + min + " and " +
            max + "." );
        return false;
      } else {
        return true;
      }
    }


    $("#dialog-form").dialog({
      autoOpen: false,
      height: 300,
      width: 350,
      modal: true,
      buttons: {
        "Create": function() {
          var bValid = true;
          allFields.removeClass("ui-state-error");

          bValid = bValid && checkLength(firstname, "firstname", 1, 128);
          bValid = bValid && checkLength(lastname, "lastname", 1, 128);
          bValid = bValid && checkLength(zipcode, "zipcode", 5, 10);

          if (bValid) {
            add_row(firstname, lastname, zipcode);
            $(this).dialog("close");
          }
        },
        Cancel: function() {
          $(this).dialog("close");
        }
      },
      close: function() {
        allFields.val("").removeClass("ui-state-error");
      }
    });


    $("#delete-message").dialog({
      autoOpen: false,
      modal: true,
      buttons: {
        Cancel: function () {
          $(this).dialog("close");
        },
        Ok: function() {
          var ids = [];
          $('#contacts')
            .find('td[class="delcol"]')
            .filter(function() {
              return $(this).find('input[type="checkbox"]:checked').length;
            })
            .each(function(i, item) {
              item = $(item);
              var id_ = item.next().text();
              if (id_ != '-1') {
                ids.push(id_);
              }
              // TODO: this needs to be in a success handler.
              item.parent().remove();
            });
          ensure_data_row();

          $.ajax({
            type: "DELETE",
            url: "/cmgr",
            data: JSON.stringify(ids),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function(json) {},
            failure: function(err) { //TODO: failure ui-state-error
            }
          });
          $(this).dialog("close");
        }
      }
    });


    $("#create-contact")
      .button()
      .click(function() {
        $("#dialog-form").dialog("open");
      });


    $("#delete-contacts")
      .button()
      .click(function() {
        $("#delete-message").dialog("open");
      });


    $("#save-contact-list")
      .button()
      .click(function() {
        var data = [];
        $('#contacts').find('tr').each(function(index, row) {
            row_data = [];
            $(row).find('td').each(function(index, cell) {
                row_data.push($(cell).html());
            });
            if (row_data.length == 7) {
                data.push(row_data);
            }
        })

        $('#contacts').mask('Saving...');

        $.ajax({
           type: "POST",
           url: "/cmgr",
           data: JSON.stringify(data),
           contentType: "application/json; charset=utf-8",
           dataType: "json",
           success: function(json) {
               // When the contacts are saved, update the -1 id cells with the
               // id saved to each new contact.
               var created = json['created'],
                   modified = json['modified'];

               $.each(created, function(i, item) {
                   $('#contacts')
                     .find('td:contains("-1"):first').text(item);
               });
           },
           failure: function(err) {
             //TODO: failure ui-state-error
           },
           complete: function(msg) {
             $('#contacts').unmask();
           }
        });
      });


    $("#reset-contact-list")
      .button()
      .click(function() {
        // "Reset" the contact list by just redirecting to the contact manager
        // again since the changes haven't been saved yet.
        window.location = '/';
      })
  });


function add_row(firstname, lastname, zipcode) {
  var firstname = firstname.val(),
      lastname = lastname.val(),
      zipcode = zipcode.val();

  $('#contacts').mask('Retrieving city and state...');

  $.ajax({
    url: ZIPTASTIC + zipcode,
    dataType: 'json',
    success: function(json) {
      $('#contacts').find('td:contains(' + NOCONTACTS+ ')').remove();

      var city = json['city'] || '',
          state = json['state'] || '';

      $("#contacts tbody").append("<tr>" +
        "<td class='delcol'><input type='checkbox' name='delete' id='delete'>" +
        "</td>" +
        "<td class='idcol'>-1</td>" +
        "<td class='edit firstname'>" + firstname + "</td>" +
        "<td class='edit lastname'>" + lastname + "</td>" +
        "<td class='edit zipcode'>" + zipcode + "</td>" +
        "<td class='city'>" + city + "</td>" +
        "<td class='state'>" + state + "</td>" +
      "</tr>");
    },
    failure: function(err) {
      //TODO
    },
    complete: function(msg) {
      $('#contacts').unmask();
    }
  });
}


function ensure_data_row() {
  if ($('#contacts').find('td').length == 0) {
    $('#contacts tbody').append(
        '<tr><td colspan="7" class="ui-state-highlight">' + NOCONTACTS +
        '</td></tr>');
  }
}


function editableFunc(value, settings) {
  // When the cell is edit, check to see if the field was a zipcode field.
  // If it was, update the City and State fields.

  if ($(this).hasClass('zipcode')) {
    $('#contacts').mask('Updating city and state...');
    $.ajax({
        url: ZIPTASTIC + value,
        dataType: 'json',
        success: function(json) {
          var city = json['city'] || '',
              state = json['state'] || '';

          $('td[class="edit zipcode"]').filter(function() {
             return $(this).text() == '28409';
          }).each(function(i, item) {
             var cityField = $(item).next();
             var stateField = cityField.next();
             cityField.text(city);
             stateField.text(state);
          });
        },
        failure: function(err) {
          //console.log('failure');
        },
        complete: function(msg) {
          $('#contacts').unmask();
        }
    });
  }

  return value;
}


$(document).ready(function() {

  ensure_data_row();

  $('#checkall').change(function() {
    $('#contacts')
      .find('input[type="checkbox"]')
      .prop("checked", $(this)
      .prop("checked"));
  });

  $('.edit').editable(editableFunc);

  // Handle dynamically added cells.
  $(document).on('click', '.edit', function(event) {
    event.preventDefault()
    $(this).editable(editableFunc);
  });
});


