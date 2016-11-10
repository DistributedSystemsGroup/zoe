import { Component } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms';
import { Router } from '@angular/router'
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'login',
  template: `
        <div *ngIf="loading" class="spinner-block">
            <div class="spinner-title">Loading...</div> <i class="spinner-icon"></i>
        </div>
        
        <div *ngIf="!loading">
          <h1>Login</h1>
          <form [formGroup]="loginForm" class="form-horizontal" id="login" (ngSubmit)="doLogin()">
              <div class="form-group">
                  <label for="inputUsername" class="col-sm-2 control-label">Username</label>
                  <div class="col-sm-4">
                      <input type="text" class="form-control" id="inputUsername" formControlName="username">
                  </div>
              </div>
              <div class="form-group">
                  <label for="inputPassword" class="col-sm-2 control-label">Password</label>
                  <div class="col-sm-4">
                      <input type="password" class="form-control" id="inputPassword" formControlName="password">
                  </div>
              </div>
              <button type="submit" class="btn btn-success" style="margin-top:20px;">Submit</button>
          </form>
        </div>
    `
})
export class LoginComponent {
  private loading: boolean = true;

  loginForm = new FormGroup({
    username: new FormControl(),
    password: new FormControl()
  });

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {
    this.showLoading();

    if (this.apiService.isUserLoggedIn()) {
      this.goToExecutionList()
    }
    else {
      if (this.apiService.isLoginNeeded()) {
        this.hideLoading();
      }
      else {
        this.apiService.getUserCredentials()
          .then(credentials => this.goToExecutionList())
          .catch(error => {
            this.hideLoading();
            this.showError('There was an error while trying to contact the server or you do not appear to be logged in with LDAP.')
          });
      }
    }
  }

  doLogin() {
    this.showLoading();

    let username = this.loginForm.controls['username'].value;
    let password = this.loginForm.controls['password'].value;

    this.apiService.login(username, password)
      .then(logged => this.loginHandler(logged))
      .catch(error => {
        this.hideLoading();
        this.showError('There was an error while trying to contact the server. Please try again later.')
      });
  }

  loginHandler(logged: Boolean) {
    if (logged)
      this.goToExecutionList();
    else {
      this.hideLoading();
      this.showError('Login failed. Please verify username and/or password.')
    }
  }

  showError(msg: string) {
    alert(msg)
  }

  showLoading() {
    this.loading = true;
  }

  hideLoading() {
    this.loading = false;
  }

  goToExecutionList() {
    this.router.navigateByUrl('executions/list')
  }
}