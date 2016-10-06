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
        <div *ngIf="!loading && execution">
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
              <dd *ngIf="execution.submitted">{{execution.submitted | toDate | date:'medium'}}</dd>
              <dd *ngIf="!execution.submitted">Not yet</dd>
              <dt *ngIf="execution.scheduled">Scheduled</dt>
              <dd *ngIf="execution.scheduled">{{execution.scheduled | toDate | date:'medium'}}</dd>
              <dt>Started</dt>
              <dd *ngIf="execution.started">{{execution.started | toDate | date:'medium'}}</dd>
              <dd *ngIf="!execution.started">Not yet</dd>
              <dt>Finished</dt>
              <dd *ngIf="execution.finished">{{execution.finished | toDate | date:'medium'}}</dd>
              <dd *ngIf="!execution.finished">Not yet</dd>
            </dl>
            
            <h3>Services</h3>
            <div *ngIf="!hasServices()" class="row">
                <div class="text-danger col-md-3 col-md-offset-1">No services</div>
            </div>
            <div *ngIf="hasServices()" class="row service-list">
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
                      <dd *ngIf="service.link()"><a [href]="service.link().url" target="_blank">{{service.link().name}}</a></dd>
                    </dl>
                </div>
            </div>
        </div>
    `
})
export class ExecutionInfoComponent implements OnInit {
  private loading = true
  private errorMessage: string
  private warningMessage: string

  private execution: Execution;
  private services: Service[]

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService
  ) { }

  ngOnInit(): void {
    this.route.params.forEach((params: Params) => {
      let id = params['id'];
      this.apiService.getExecutionDetails(id)
        .then(execution => this.setExecutionDetails(execution))
        .catch(error => this.showError('Execution not found.'));
    });
  }

  hasServices(): Boolean {
    return this.services && (this.services.length > 0)
  }

  setExecutionDetails(execution: Execution) {
    this.execution = execution
    this.getServicesDetails(execution)
  }

  getServicesDetails(execution: Execution) {
    if (execution.services && execution.services.length > 0) {
      this.services = []

      var errors = false
      for (let srv of execution.services) {
        this.apiService.getServiceDetails(srv.toString())
          .then(service => this.services.push(service))
          .catch(error => errors = true);
      }
      if (errors)
        this.showWarning('Failed to retrieve one or more services.');

      this.hideLoading()
    }
  }

  showLoading() {
    this.loading = true
  }

  hideLoading() {
    this.loading = false
  }

  showError(msg: string) {
    this.hideLoading()
    this.errorMessage = msg
  }

  showWarning(msg: string) {
    this.hideLoading()
    this.warningMessage = msg
  }
}
