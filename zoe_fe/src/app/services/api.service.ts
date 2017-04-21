import { Injectable } from '@angular/core';
import { SoftwareInfo } from '../entities/software-info';
import { Headers, Http } from '@angular/http';
import { Execution } from '../entities/execution';
import { Service } from '../entities/service';
import { Credentials } from '../entities/credentials';
import { ServiceDiscovery } from '../entities/service-discovery';
import { Statistics } from '../entities/statistics';

import { environment } from '../../environments/environment';

import 'rxjs/add/operator/toPromise';
import { StorageService } from './storage.service';

let AUTH_HEADERS: string = 'AUTH_HEADERS';

@Injectable()
export class ApiService {
  private baseUrl = environment.apiEndpoint;

  private userInfoEndpoint = '/userinfo';
  private loginEndpoint = '/login';

  private softwareInfoEndpoint = '/info';
  private executionEndpoint = '/execution';
  private deleteExecutionEndpoint = '/execution/delete';
  private serviceEndpoint = '/service';
  private serviceDiscoveryEndpoint = '/discovery/by_group';
  private statisticsEndpoint = '/statistics/scheduler';

  constructor(
    private http: Http,
    private storageService: StorageService
  ) { }

  private isAuthLDAP(): Boolean {
    return (environment.auth.type == 'ldap')
  }

  private getHeaders(): {[key: string]: any} {
    let options = null;

    if (!this.isAuthLDAP()) {
      options = {headers: this.storageService.getAuthHeader()}
    }

    return options
  }

  isLoginNeeded(): Boolean {
    return (!this.isAuthLDAP() || (!environment.auth.kerberos && !environment.auth.adfs))
  }

  isUserLoggedIn(): Boolean {
    return (this.storageService.getCredentials() != null);
  }

  logout() {
    this.removeCookie('zoe');
    this.storageService.removeAuthHeader();
    this.storageService.removeCredentials();
  }

  createCookie(name: string, value: string, days: number) {
    if (days) {
      var date = new Date();
      date.setTime(date.getTime() + (days*24*60*60*1000));
      var expires = "; expires=" + date.toUTCString();
    }
    else var expires = "";
    document.cookie = name + "=" + value + expires + "; path=/";
  }

  removeCookie(name: string) {
    this.createCookie(name, "", -1);
  }

  removeAllCookies() {
    let cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++)
      this.removeCookie(cookies[i].split("=")[0]);
  }
  
  getUserCredentials(): Promise<Credentials> {
    if (this.isAuthLDAP()) {
      this.storageService.removeCredentials();

      return this.http.get(this.baseUrl + this.userInfoEndpoint)
          .toPromise()
          .then(response => {
            let credentials = new Credentials().deserialize(response.json());
            this.storageService.setCredentials(credentials);

            return credentials;
          })
          .catch(this.handleError);
    }

    return Promise.resolve(null)
  }

  loginHandler(username: string, headers: Headers, response: any): Boolean {
    this.storageService.removeAuthHeader();
    this.storageService.removeCredentials();
    this.storageService.removeUsername();

    if (!response.ok) {
      return false;
    }

    if (response.status === 401) {
      return false;
    }

    if (response.status === 200) {
      let credentials = new Credentials().deserialize(response.json());
      this.storageService.setCredentials(credentials);
      this.storageService.setAuthHeader(headers);
      return true;
    }

    return false;
  }

  login(username: string, password: string): Promise<Boolean> {
    let headers = new Headers();
    headers.append('Authorization', 'Basic ' +
      btoa(username + ':' + password));

    let endpoint: string = this.baseUrl + this.loginEndpoint

    return this.http.get(endpoint, { headers: headers })
      .toPromise()
      .then(response => this.loginHandler(username, headers, response))
      .catch(this.handleError);
  }

  getSoftwareInfo(): Promise<SoftwareInfo> {
    let endpoint: string = this.baseUrl + this.softwareInfoEndpoint;

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new SoftwareInfo().deserialize(response.json()))
      .catch(this.handleError);
  }

  getExecutionDetails(id: string): Promise<Execution> {
    let endpoint: string = this.baseUrl + this.executionEndpoint + '/' + id;

    return this.http.get(endpoint, this.getHeaders())
      .toPromise()
      .then(response => new Execution().deserialize(response.json()))
      .catch(this.handleError);
  }

  terminateExecution(id: string): Promise<Boolean> {
    let endpoint: string = this.baseUrl + this.executionEndpoint + '/' + id;

    return this.http.delete(endpoint, this.getHeaders())
      .toPromise()
      .then(response => Boolean(response.status === 204))
      .catch(this.handleError);
  }

  deleteExecution(id: string): Promise<Boolean> {
    let endpoint: string = this.baseUrl + this.deleteExecutionEndpoint + '/' + id;

    return this.http.delete(endpoint, this.getHeaders())
      .toPromise()
      .then(response => Boolean(response.status === 204))
      .catch(this.handleError);
  }

  getAllExecutions(): Promise<Execution[]> {
    let endpoint: string = this.baseUrl + this.executionEndpoint;

    return this.http.get(endpoint, this.getHeaders())
      .toPromise()
      .then(response => {
        let executionsList: Execution[] = [];

        Object.keys(response.json()).forEach(key => {
          executionsList.push(new Execution().deserialize(response.json()[key]));
        });
        return executionsList;
      })
      .catch(this.handleError);
  }

  startExecution(name: string, application: Object): Promise<number> {
    let endpoint: string = this.baseUrl + this.executionEndpoint;

    let jsonData = {
      'name': name,
      'application': application
    };

    return this.http.post(endpoint, JSON.stringify(jsonData), this.getHeaders())
      .toPromise()
      .then(response => response.json().execution_id)
      .catch(this.handleError);
  }

  getServiceDetails(id: string): Promise<Service> {
    let endpoint: string = this.baseUrl + this.serviceEndpoint + '/' + id;

    return this.http.get(endpoint, this.getHeaders())
      .toPromise()
      .then(response => new Service().deserialize(response.json()))
      .catch(this.handleError);
  }

  discoverServices(executionId: string, serviceType: string): Promise<ServiceDiscovery> {
    let endpoint: string = this.baseUrl + this.serviceDiscoveryEndpoint + '/' + executionId + '/' + serviceType;

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new ServiceDiscovery().deserialize(response.json()))
      .catch(this.handleError);
  }

  getStatistics(): Promise<Statistics> {
    let endpoint: string = this.baseUrl + this.statisticsEndpoint;

    return this.http.get(endpoint)
      .toPromise()
      .then(response => new Statistics().deserialize(response.json()))
      .catch(this.handleError);
  }

  private handleError(error: any): Promise<any> {
    if (!environment.production) {
      console.error('An error occurred', error); // for demo purposes only
    }
    return Promise.reject(error.message || error);
  }
}