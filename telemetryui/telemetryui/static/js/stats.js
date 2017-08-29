/*
 * Copyright 2017 Intel Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

(function(root, factory){

    factory(root);

})(this.telemetryUI, function(rootObj){


    function renderStats(ctx, title, labels, values){

        var data = {
            labels: labels,
            datasets: [{
                label: title,
                backgroundColor: rootObj.backgroundColors,
                data: values
            }]
        };

        var options = {
            title: {
                display: true,
                fontSize: 18,
                text: title
            },
            legend: {
                display: false
            }
        };

        rootObj.newChart(ctx, "pie", data, options);
    }

    var renderStatsPlatform = renderStats;
    var renderStatsClass = renderStats;


    rootObj.renderStatsClass = renderStatsClass;
    rootObj.renderStatsPlatform = renderStatsPlatform;

});
