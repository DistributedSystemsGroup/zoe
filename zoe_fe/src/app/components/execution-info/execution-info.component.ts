import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Params } from '@angular/router';
import { Execution } from '../../entities/execution';
import { Service } from '../../entities/service';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'execution-info',
  template: `
        <div *ngIf="errorMessage" class="alert alert-danger alert-dismissible fade in" role="alert">
          {{errorMessage}}
        </div>
        <div *ngIf="warningMessage" class="alert alert-warning alert-dismissible fade in" role="alert">
          {{warningMessage}}
        </div>
        
        <div *ngIf="loading" class="spinner-block">
            <div class="spinner-title">Loading...</div> <i class="spinner-icon"></i>
        </div>
        <div *ngIf="!loading && execution" id="execution-details">
            <h1>Execution <em>{{execution.id}}</em></h1>
            <hr />
            <h3>Details</h3>
            <dl class="dl-horizontal">
              <dt>Name</dt>
              <dd>{{execution.name}}</dd>
              <dt>Application name</dt>
              <dd>{{execution.applicationName()}}</dd>
              <dt>Owner</dt>
              <dd>{{execution.owner}}</dd>
              <dt>Status</dt>
              <dd>{{execution.status}}</dd>
              <dt>Submitted</dt>
              <dd *ngIf="execution.submitted">{{execution.submitted | amFromUnix | amDateFormat:'MMM D, YYYY, h:mm:ss a'}}</dd>
              <dd *ngIf="!execution.submitted">Not yet</dd>
              <dt *ngIf="execution.scheduled">Scheduled</dt>
              <dd *ngIf="execution.scheduled">{{execution.scheduled | amFromUnix | amDateFormat:'MMM D, YYYY, h:mm:ss a'}}</dd>
              <dt>Started</dt>
              <dd *ngIf="execution.started">{{execution.started | amFromUnix | amDateFormat:'MMM D, YYYY, h:mm:ss a'}}</dd>
              <dd *ngIf="!execution.started">Not yet</dd>
              <dt>Finished</dt>
              <dd *ngIf="execution.finished">{{execution.finished | amFromUnix | amDateFormat:'MMM D, YYYY, h:mm:ss a'}}</dd>
              <dd *ngIf="!execution.finished">Not yet</dd>
            </dl>
            
            <h3>Services</h3>
            <div *ngIf="loadingServices" class="spinner-block">
                <div class="spinner-title">Loading...</div> <i class="spinner-icon"></i>
            </div>
            <div *ngIf="!loadingServices && !hasServices()" class="row">
                <div class="text-danger col-md-3 col-md-offset-1">No services</div>
            </div>
            <div *ngIf="!loadingServices && hasServices()" class="row service-list" id="execution-service">
                <div class="col-md-6">
                    <dl *ngFor="let service of services" class="dl-horizontal">
                      <dt>Id</dt>
                      <dd>{{service.id}}</dd>
                      <dt>Name</dt>
                      <dd>{{service.name}}</dd>
                      <dt>Zoe Status</dt>
                      <dd>{{service.status | capitalize}}</dd>
                      <dt>Docker Status</dt>
                      <dd>{{service.dockerStatus | capitalize}}</dd>
                      <dt *ngIf="service.link()">Link</dt>
                      <dd *ngIf="service.link()"><a [href]="'http://'+service.link().url" target="_blank">{{service.link().name}}</a></dd>
                    </dl>
                </div>
            </div>
        </div>
    `
})
export class ExecutionInfoComponent implements OnInit {
  private loading = true;
  private loadingServices = true;
  private errorMessage: string;
  private warningMessage: string;

  private execution: Execution;
  private services: Service[];

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService
  ) { }

  ngOnInit(): void {
    this.route.params.forEach((params: Params) => {
      let id = params['id'];
      this.apiService.getExecutionDetails(id)
        .then(execution => {
          this.setExecutionDetails(execution);
          this.hideLoading();
        })
        .catch(error => {
          this.showError('Execution not found.');
          this.hideLoading();
        });
    });
  }

  hasServices(): Boolean {
    return this.services && (this.services.length > 0);
  }

  setExecutionDetails(execution: Execution) {
    this.execution = execution;
    this.getServicesDetails(execution);
  }

  getServicesDetails(execution: Execution) {
    if (execution.services && execution.services.length > 0) {
      this.services = [];

      let errors = false;
      let activeRequests = 0;
      for (let srv of execution.services) {
        activeRequests += 1;
        this.apiService.getServiceDetails(srv.toString())
          .then(service => {
            this.services.push(service);
            activeRequests -= 1;
            this.serviceDetailsHandler(activeRequests, errors);
          })
          .catch(error => {
            errors = true;
            activeRequests -= 1;
            this.serviceDetailsHandler(activeRequests, errors);
          });
      }
    }
  }

  serviceDetailsHandler(activeRequests: number, errors: boolean) {
    if (errors) {
      this.showWarning('Failed to retrieve one or more services.');
    }

    if (activeRequests == 0) {
      this.hideServicesLoading();
    }
  }

  showLoading() {
    this.loading = true;
  }

  hideLoading() {
    this.loading = false;
  }

  showServicesLoading() {
    this.loadingServices = true;
  }

  hideServicesLoading() {
    this.loadingServices = false;
  }

  showError(msg: string) {
    this.hideLoading();
    this.hideServicesLoading();
    this.errorMessage = msg;
  }

  showWarning(msg: string) {
    this.hideLoading();
    this.hideServicesLoading();
    this.warningMessage = msg;
  }
}
