import { Component, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'execution-new',
  template: `
        <h1>New Execution</h1>
        <form class="form-horizontal" id="execution-new" (ngSubmit)="startExecution($event)">
            <div class="form-group">
                <label for="inputName" class="col-sm-2 control-label">Name</label>
                <div class="col-sm-10">
                    <input type="name" class="form-control" id="inputName" placeholder="Enter a name" (keyup)="onNameKeyup($event)" (keypress)="onNameKeypress($event)">
                </div>
            </div>
            <div class="form-group">
                <label for="inputDescription" class="col-sm-2 control-label">Description</label>
                <div class="col-sm-10">
                    <label class="btn btn-default btn-file">
                        Browse <input type="file" style="display: none;" accept="application/json" (change)="onFileChange($event)">
                    </label>
                    <span #fileMessage style="margin-left: 10px;">Please select a valid JSON file</span>
                </div>
            </div>
            <button type="submit" class="btn btn-success" style="margin-top:20px;" [disabled]="!canBeSubmitted()">Submit</button>
        </form>
    `
})
export class ExecutionNewComponent implements AfterViewInit {
  @ViewChild('fileMessage') fileMessage: ElementRef;

  private executionName: string
  private application: Object

  constructor(
    private apiService: ApiService,
    private router: Router
  ) { }

  ngAfterViewInit() {
  }

  startExecution() {
    this.apiService.startExecution(this.executionName, this.application)
      .then(executionId => this.router.navigateByUrl('executions/' + executionId))
      .catch(error => alert('There was a problem creating the new execution, please try again.'));
  }

  onNameKeypress(e): boolean {
    e = e || window.event;
    var charCode = (typeof e.which == "undefined") ? e.keyCode : e.which;
    var charStr = String.fromCharCode(charCode);
    return /^([A-Za-z0-9\-]+)$/.test(charStr)
  }

  onNameKeyup(event) {
    this.executionName = event.srcElement.value
  }

  onFileChange(event) {
    let file = event.srcElement.files[0]
    let component = this

    var myReader: FileReader = new FileReader();
    myReader.onloadend = function(e){
      let data: string = myReader.result
      try {
        component.application = JSON.parse(data)
        component.setFilenameToDisplay(file.name)
      } catch(e) {
        component.setFilenameToDisplay('Selected file is not a valid JSON file.')
      }
    }

    myReader.readAsText(file)
  }

  setFilenameToDisplay(text: string) {
    this.fileMessage.nativeElement.textContent = text
  }

  canBeSubmitted(): boolean {
    return ((this.executionName != null) && this.executionName.length > 3 && (this.application != null))
  }
}
