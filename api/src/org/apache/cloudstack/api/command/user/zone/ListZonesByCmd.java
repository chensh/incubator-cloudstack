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
package org.apache.cloudstack.api.command.user.zone;

import java.util.ArrayList;
import java.util.List;

import org.apache.cloudstack.api.APICommand;
import org.apache.cloudstack.api.response.DomainResponse;
import org.apache.log4j.Logger;

import org.apache.cloudstack.api.ApiConstants;
import org.apache.cloudstack.api.BaseListCmd;
import org.apache.cloudstack.api.Parameter;
import org.apache.cloudstack.api.response.ListResponse;
import org.apache.cloudstack.api.response.ZoneResponse;
import com.cloud.dc.DataCenter;

@APICommand(name = "listZones", description="Lists zones", responseObject=ZoneResponse.class)
public class ListZonesByCmd extends BaseListCmd {
    public static final Logger s_logger = Logger.getLogger(ListZonesByCmd.class.getName());

    private static final String s_name = "listzonesresponse";

    /////////////////////////////////////////////////////
    //////////////// API parameters /////////////////////
    /////////////////////////////////////////////////////
    @Parameter(name=ApiConstants.ID, type=CommandType.UUID, entityType=ZoneResponse.class,
            description= "the ID of the zone")
    private Long id;

    @Parameter(name=ApiConstants.AVAILABLE, type=CommandType.BOOLEAN,
            description="true if you want to retrieve all available Zones. False if you only want to return the Zones" +
                    " from which you have at least one VM. Default is false.")
    private Boolean available;

    @Parameter(name=ApiConstants.DOMAIN_ID, type=CommandType.UUID, entityType=DomainResponse.class,
            description="the ID of the domain associated with the zone")
    private Long domainId;

    @Parameter(name=ApiConstants.SHOW_CAPACITIES, type=CommandType.BOOLEAN, description="flag to display the capacity of the zones")
    private Boolean showCapacities;

    /////////////////////////////////////////////////////
    /////////////////// Accessors ///////////////////////
    /////////////////////////////////////////////////////

    public Long getId() {
        return id;
    }

    public Boolean isAvailable() {
        return available;
    }

    public Long getDomainId(){
        return domainId;
    }

    public Boolean getShowCapacities() {
        return showCapacities;
    }

    /////////////////////////////////////////////////////
    /////////////// API Implementation///////////////////
    /////////////////////////////////////////////////////

    @Override
    public String getCommandName() {
        return s_name;
    }

    @Override
    public void execute(){
        List<? extends DataCenter> dataCenters = _mgr.listDataCenters(this);
        ListResponse<ZoneResponse> response = new ListResponse<ZoneResponse>();
        List<ZoneResponse> zoneResponses = new ArrayList<ZoneResponse>();
        for (DataCenter dataCenter : dataCenters) {
            ZoneResponse zoneResponse = _responseGenerator.createZoneResponse(dataCenter, showCapacities);
            zoneResponse.setObjectName("zone");
            zoneResponses.add(zoneResponse);
        }

        response.setResponses(zoneResponses);
        response.setResponseName(getCommandName());
        this.setResponseObject(response);
    }
}
