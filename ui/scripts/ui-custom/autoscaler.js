// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

(function($, cloudStack) {
  cloudStack.uiCustom.autoscaler = function(args) {
    // Place outer args here as local variables
    // i.e, -- var dataProvider = args.dataProvider
    var forms = $.extend(true, {}, args.forms);
    var topfields = forms.topFields;
    var bottomfields = forms.bottomFields;
    var scaleuppolicy = forms.scaleUpPolicy;
    var scaledownpolicy = forms.scaleDownPolicy;
    var dataProvider = cloudStack.autoscaler.dataProvider;

    return function(args) {
      var context = args.data ?
            $.extend(true, {}, args.context, {
              lbRules: [args.data]
            }) : args.context;
      var formData = args.formData;
      var $autoscalerDialog = $('<div>').addClass('autoscaler');
      var $topFields = $('<div>').addClass('field-group top-fields');
      var $bottomFields = $('<div>').addClass('field-group bottom-fields');
      var $scaleUpPolicy = $('<div>').addClass('scale-up-policy');
      var $slideScaleUp = $('<div></div>').addClass('expand');
      var $hideScaleUp = $('<div></div>').addClass('hide');
      var $scaleUpLabel= $('<div>Show</div>').addClass('slide-label');
      var $scaleUpHideLabel=$('<div>Hide</div>').addClass('slide-label');
      var $scaleDownHideLabel=$('<div>Hide</div>').addClass('slide-label');
      var $scaleDownLabel=$('<div>Show</div>').addClass('slide-label');
      var $slideScaleDown = $('<div></div>').addClass('expand');
      var $hideScaleDown = $('<div></div>').addClass('hide');
      var $scaleUpDivider = $('<hr></hr>').addClass('policy-divider');
      var $scaleDownDivider = $('<hr></hr>').addClass('policy-divider');
      var $bottomFieldDivider = $('<hr></hr>').addClass('policy-divider');
      var $scaleDownPolicy = $('<div>').addClass('scale-down-policy');
      var $scaleUpPolicyTitle = $('<div>').addClass('scale-up-policy-title')
            .html("Scale Up Policy");
      var $scaleDownPolicyTitle = $('<div>').addClass('scale-down-policy-title')
            .html("Scale Down Policy");
      var topFieldForm, $topFieldForm,
          bottomFieldForm, $bottomFieldForm,
          scaleUpPolicyTitleForm, $scaleUpPolicyTitleForm,
          scaleDownPolicyTitleForm, $scaleDownPolicyTitleForm,
          scaleUpPolicyForm, scaleDownPolicyForm;

      var renderDialogContent = function(args) {
        var data = args.data ? args.data : {};

        // Setup default values, in case where existing data is present
        var setDefaultFields = function(fieldID, field) {
          var fieldData = data[fieldID];

          if (fieldData && !field.isBoolean) {
            field.defaultValue = fieldData;
          } else {
            field.isChecked = fieldData;
          }
        };
        $.each(topfields, setDefaultFields);
        $.each(bottomfields, setDefaultFields);

        // Create and append top fields
        // -- uses create form to generate fields
        topFieldForm = cloudStack.dialog.createForm({
          context: context,
          noDialog: true, // Don't render a dialog, just return $formContainer
          form: {
            title: '',
            fields: topfields
          }
        });
        $topFieldForm = topFieldForm.$formContainer;
        $topFieldForm.appendTo($topFields);

        scaleUpPolicyTitleForm = cloudStack.dialog.createForm({
          context: context,
          noDialog: true,
          form: {
            title: '',
            fields: {
              scaleUpDuration: { label: 'Duration', validation: { required: true } }
            }
          }
        });
        $scaleUpPolicyTitleForm = scaleUpPolicyTitleForm.$formContainer;
        $scaleUpPolicyTitleForm.appendTo($scaleUpPolicyTitle);


        scaleDownPolicyTitleForm = cloudStack.dialog.createForm({
          context: context,
          noDialog: true,
          form: {
            title: '',
            fields: {
              scaleDownDuration: { label: 'Duration', validation: { required: true } }
            }
          }
        });
        $scaleDownPolicyTitleForm = scaleDownPolicyTitleForm.$formContainer;
        $scaleDownPolicyTitleForm.appendTo($scaleDownPolicyTitle);

        // Make multi-edits
        //
        // Scale up policy
        if (data.scaleUpPolicy && $.isArray(data.scaleUpPolicy.conditions)) {
          $autoscalerDialog.data('autoscaler-scale-up-data',
                                 data.scaleUpPolicy.conditions);
        }

        if (data.scaleUpPolicy && data.scaleUpPolicy.duration) {
          $scaleUpPolicyTitleForm.find('input[name=scaleUpDuration]').val(
            data.scaleUpPolicy.duration
          );
        }

        scaleuppolicy.context = context;
        scaleUpPolicyForm = $scaleUpPolicy.multiEdit(scaleuppolicy);

        // Scale down policy
        if (data.scaleDownPolicy && $.isArray(data.scaleDownPolicy.conditions)) {
          $autoscalerDialog.data('autoscaler-scale-down-data',
                                 data.scaleDownPolicy.conditions);
        }

        if (data.scaleDownPolicy && data.scaleDownPolicy.duration) {
          $scaleDownPolicyTitleForm.find('input[name=scaleDownDuration]').val(
            data.scaleDownPolicy.duration
          );
        }

        scaledownpolicy.context = context;
        scaleDownPolicyForm = $scaleDownPolicy.multiEdit(scaledownpolicy);

        // Create and append bottom fields
        bottomFieldForm = cloudStack.dialog.createForm({
          context: context,
          noDialog: true, // Don't render a dialog, just return $formContainer
          form: {
            title: '',
            fields: bottomfields
          }
        });
        $bottomFieldForm = bottomFieldForm.$formContainer;
        $bottomFieldForm.appendTo($bottomFields);

        // Append main div elements
        $autoscalerDialog.append(
          $topFields,
          $scaleUpPolicyTitle,
          $scaleUpPolicy,
          $scaleDownPolicyTitle,
          $scaleDownPolicy,
          $bottomFields
        );

        // Render dialog
        //$autoscalerDialog.find('.form-item[rel=templateNames] label').hide();
        /* Duration Fields*/
        //$('div.ui-dialog div.autoscaler').find('div.scale-up-policy-title').append("<br></br>").append($inputLabel = $('<label>').html('Duration').attr({left:'200'})).append($('<input>').attr({ name: 'username' }));
        //$('div.ui-dialog div.autoscaler').find('div.scale-down-policy-title').append("<br></br>").append($inputLabel = $('<label>').html('Duration').attr({left:'200'})).append($('<input>').attr({ name: 'username' }));

        /*Dividers*/
        $autoscalerDialog.find('div.scale-up-policy-title').prepend($scaleUpDivider);
        $autoscalerDialog.find('div.scale-down-policy-title').prepend($scaleDownDivider);
        $autoscalerDialog.find('div.field-group.bottom-fields').prepend($bottomFieldDivider);

        /* Hide effects for multi-edit table*/
        $autoscalerDialog.find('div.scale-up-policy').prepend($hideScaleUp);
        $autoscalerDialog.find('div.scale-down-policy ').prepend($hideScaleDown);
        $autoscalerDialog.find('div.scale-up-policy').prepend($scaleUpHideLabel);
        $autoscalerDialog.find('div.scale-down-policy').prepend($scaleDownHideLabel);

        /*Toggling the labels and data-item table - SCALE UP POLICY*/
        $autoscalerDialog.find('div.scale-up-policy div.hide').click(function() {
          $autoscalerDialog.find('div.scale-up-policy div.multi-edit div.data-item').slideToggle();
          $scaleUpLabel = $autoscalerDialog.find('div.scale-up-policy div.slide-label').replaceWith($scaleUpLabel);
        });

        /*Toggling the images */
        $('div.ui-dialog div.autoscaler div.scale-up-policy div.hide').click(function() {
          $(this).toggleClass('expand hide');
        });

        $('div.ui-dialog div.autoscaler div.scale-down-policy div.hide').click(function() {
          $(this).toggleClass('expand hide');
        });

        /*Toggling the labels and data-item table - SCALE DOWN POLICY*/
        $('div.ui-dialog div.autoscaler div.scale-down-policy div.hide').click(function() {
          $('div.ui-dialog div.autoscaler div.scale-down-policy div.multi-edit div.data div.data-item').slideToggle();
          $scaleDownLabel = $('div.ui-dialog div.autoscaler div.scale-down-policy div.slide-label').replaceWith($scaleDownLabel);
        });

        $('div.ui-dialog div.autoscaler div.scale-down-policy div.multi-edit div.data div.expand').click(function() { $('div.ui-dialog div.autoscaler div.scale-down-policy div.multi-edit div.data div.data-item').slideToggle(); });

        $autoscalerDialog.dialog('option', 'position', 'center');
        $autoscalerDialog.dialog('option', 'height', 'auto');
      };

      var $loading = $('<div>').addClass('loading-overlay').appendTo($autoscalerDialog);
      $autoscalerDialog.dialog({
        title: 'AutoScale Configuration Wizard',
        width: 825,
        height: 600,
        draggable: true,
        closeonEscape: false,
        overflow:'auto',
        open:function() {
          $("button").each(function(){
            $(this).attr("style", "left: 600px; position: relative; margin-right: 5px; ");
          });
        },
        buttons: [
          {
            text: _l('label.cancel'),
            'class': 'cancel',
            click: function() {
              $autoscalerDialog.dialog('destroy');
              $('.overlay').remove();
            }
          },
          {
            text: _l('Apply'),
            'class': 'ok',
            click: function() {
              var data = cloudStack.serializeForm($('.ui-dialog .autoscaler form'));

              $loading.appendTo($autoscalerDialog);
              cloudStack.autoscaler.actions.add({
                formData: formData,
                context: context,
                data: data,
                response: {
                  success: function() {
                    $loading.remove();
                    $autoscalerDialog.dialog('destroy');
                    $autoscalerDialog.closest(':ui-dialog').remove();
                    $('.overlay').remove();
                    cloudStack.dialog.notice({
                      message: 'Autoscaler configured successfully.'
                    });
                  },
                  error: function(message) {
                    cloudStack.dialog.notice({ message: message });
                    $loading.remove();
                  }
                }
              });
            }
          }
        ]
      }).closest('.ui-dialog').overlay();

      dataProvider({
        context: context,
        response: {
          success: function(args) {
            $loading.remove();
            renderDialogContent(args);

            if (args.data && args.data.isAdvanced) {
              $autoscalerDialog.find('input[type=checkbox]').trigger('click');
              $autoscalerDialog.find('input[type=checkbox]').attr('checked', 'checked');
            }
          }
        }
      });
    };
  };
}(jQuery, cloudStack));