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
package org.apache.cloudstack.api.command.user.template;

import org.apache.cloudstack.api.*;
import org.apache.cloudstack.api.response.UserVmResponse;
import org.apache.cloudstack.api.response.ZoneResponse;
import org.apache.log4j.Logger;

import org.apache.cloudstack.api.APICommand;
import org.apache.cloudstack.api.response.SuccessResponse;
import com.cloud.async.AsyncJob;
import com.cloud.event.EventTypes;
import com.cloud.template.VirtualMachineTemplate;
import com.cloud.user.Account;
import com.cloud.user.UserContext;

@APICommand(name = "deleteTemplate", responseObject=SuccessResponse.class, description="Deletes a template from the system. All virtual machines using the deleted template will not be affected.")
public class DeleteTemplateCmd extends BaseAsyncCmd {
    public static final Logger s_logger = Logger.getLogger(DeleteTemplateCmd.class.getName());
    private static final String s_name = "deletetemplateresponse";

    /////////////////////////////////////////////////////
    //////////////// API parameters /////////////////////
    /////////////////////////////////////////////////////

    @Parameter(name=ApiConstants.ID, type=CommandType.UUID, entityType = UserVmResponse.class,
            required=true, description="the ID of the template")
    private Long id;

    @Parameter(name=ApiConstants.ZONE_ID, type=CommandType.UUID, entityType = ZoneResponse.class,
            description="the ID of zone of the template")
    private Long zoneId;


    /////////////////////////////////////////////////////
    /////////////////// Accessors ///////////////////////
    /////////////////////////////////////////////////////

    public Long getId() {
        return id;
    }

    public Long getZoneId() {
        return zoneId;
    }


    /////////////////////////////////////////////////////
    /////////////// API Implementation///////////////////
    /////////////////////////////////////////////////////

    @Override
    public String getCommandName() {
        return s_name;
    }

    public static String getStaticName() {
        return s_name;
    }

    @Override
    public long getEntityOwnerId() {
        VirtualMachineTemplate template = _entityMgr.findById(VirtualMachineTemplate.class, getId());
        if (template != null) {
            return template.getAccountId();
        }

        return Account.ACCOUNT_ID_SYSTEM;
    }

    @Override
    public String getEventType() {
        return EventTypes.EVENT_TEMPLATE_DELETE;
    }

    @Override
    public String getEventDescription() {
        return "Deleting template " + getId();
    }

    public AsyncJob.Type getInstanceType() {
        return AsyncJob.Type.Template;
    }

    public Long getInstanceId() {
        return getId();
    }

    @Override
    public void execute(){
        UserContext.current().setEventDetails("Template Id: "+getId());
        boolean result = _templateService.deleteTemplate(this);
        if (result) {
            SuccessResponse response = new SuccessResponse(getCommandName());
            this.setResponseObject(response);
        } else {
            throw new ServerApiException(ApiErrorCode.INTERNAL_ERROR, "Failed to delete template");
        }
    }
}
