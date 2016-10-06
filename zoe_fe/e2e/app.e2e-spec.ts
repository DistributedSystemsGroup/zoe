import { ZoePortingPage } from './app.po';

describe('zoe-porting App', function() {
  let page: ZoePortingPage;

  beforeEach(() => {
    page = new ZoePortingPage();
  });

  it('should display message saying app works', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('app works!');
  });
});
