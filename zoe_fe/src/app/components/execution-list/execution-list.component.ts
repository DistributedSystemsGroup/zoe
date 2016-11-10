import { Component, OnInit } from '@angular/core';
import { Execution } from '../../entities/execution';
import { ApiService } from '../../services/api.service';
import { StorageService } from '../../services/storage.service';
import { Router } from '@angular/router'

@Component({
  selector: 'execution-list',
  template: `
        <div *ngIf="errorMessage" class="alert alert-danger alert-dismissible fade in" role="alert">
          {{errorMessage}}
        </div>
        
        <div *ngIf="loading" class="spinner-block">
            <div class="spinner-title">Loading...</div> <i class="spinner-icon"></i>
        </div>
        <div *ngIf="executionToDisplay()">
            <div *ngIf="executionToDisplay().length > 0">
                <h1 style="display:inline-block">Executions list</h1>
                <button type="button" class="btn btn-default" [class.active]="adminMode" style="display:inline-block;float:right;" (click)="changeAdminMode()">{{ buttonTitle() }}</button>
                <div class="table-responsive" id="executions-list-table">
                    <table class="table table-hover table-striped">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Execution Name</th>
                                <th>User</th>
                                <th>Status</th>
                                <th>Scheduled</th>
                                <th>Started</th>
                                <th>Finished</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr *ngFor="let execution of executionToDisplay()" [id]="['execution-'+execution.id]">
                                <td><a [routerLink]="['/executions/'+execution.id]">{{execution.id}}</a></td>
                                <td>{{execution.name}}</td>
                                <td>{{execution.owner}}</td>
                                <td>{{execution.status | capitalize}}</td>
                                <td><div *ngIf="execution.scheduled">{{execution.scheduled | amFromUnix | amDateFormat:'MMM D, YYYY, h:mm:ss a'}}</div></td>
                                <td><div *ngIf="execution.started">{{execution.started | amFromUnix | amDateFormat:'MMM D, YYYY, h:mm:ss a'}}</div></td>
                                <td><div *ngIf="execution.ended">{{execution.ended | amFromUnix | amDateFormat:'MMM D, YYYY, h:mm:ss a'}}</div></td>
                                <td>
                                    <a href="javascript:void(0)" *ngIf="execution.canBeRestarted()" (click)="restartExecution(execution)">Restart</a>
                                    <a href="javascript:void(0)" *ngIf="execution.canBeDeleted()" (click)="deleteExecution(execution.id)">Delete</a>
                                    <a href="javascript:void(0)" *ngIf="execution.canBeTerminated()" (click)="terminateExecution(execution.id)">Terminate</a>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div *ngIf="executionToDisplay().length <= 0">
                <h1>No Executions</h1>
            </div>
        </div>
    `
})
export class ExecutionListComponent implements OnInit {
  private adminMode = true;
  private loading = false;
  private errorMessage: string;
  private executionsList: Execution[];

  closeResult: string;

  constructor(
    private apiService: ApiService,
    private router: Router,
    private storageService: StorageService
  ) { }

  ngOnInit(): void {
    let credentials = this.storageService.getCredentials();
    this.adminMode = credentials.isAdmin();
    this.getExecutions();
  }

  getExecutions() : void {
    this.showLoading();
    this.apiService.getAllExecutions()
      .then(executions => {
        this.executionsList = executions;
        this.hideLoading();
        this.hideError();

        // check if any execution has "starting" status, if so, refresh the list after 5sec
        if (this.executionsList.filter(execution => execution.status == 'starting').length > 0) {
          setTimeout(this.getExecutions(), 5000);
        }
        // check if any execution has "cleaning up" status, if so, refresh the list after 5sec
        else if (this.executionsList.filter(execution => execution.status == 'cleaning up').length > 0) {
          setTimeout(this.getExecutions(), 5000);
        }
      })
      .catch(error => {
        this.showError('There was an error contactning the server. Please try again later.');
        this.hideLoading()
      });
  }

  restartExecution(execution: Execution) {
    this.showLoading();
    this.apiService.startExecution(execution.name, execution.description.rawObject)
      .then(executionId => this.router.navigateByUrl('executions/' + executionId))
      .catch(error => {
        this.showError('There was an error while trying to restart this execution. Please try again.');
        this.hideLoading()
      })
  }

  deleteExecution(id: string) {
    this.apiService.deleteExecution(id)
      .then(terminated => {
        if (terminated)
          this.getExecutions();
        else {
          this.showError('Error while trying to delete execution ' + id);
          this.hideLoading()
        }
      });
  }

  terminateExecution(id: string) {
    this.apiService.terminateExecution(id)
      .then(terminated => {
        if (terminated)
          this.getExecutions();
        else {
          this.showError('Error while trying to terminate execution ' + id);
          this.hideLoading()
        }
      });
  }

  changeAdminMode() {
    this.adminMode = !this.adminMode
  }

  buttonTitle() : string {
    if (this.adminMode)
      return 'View all';
    else
      return 'View mine';
  }

  showLoading() {
    this.loading = true;
  }

  hideLoading() {
    this.loading = false;
  }

  executionToDisplay(): Execution[] {
    if (this.executionsList) {
      if (this.adminMode)
        return this.executionsList;
      else
        return this.executionsList.filter(execution => execution.owner == this.storageService.getUsername());
    }
    else
      return null;
  }

  showError(msg: string) {
    this.hideLoading();
    this.errorMessage = msg;
  }

  hideError() {
    this.errorMessage = null;
  }
}
